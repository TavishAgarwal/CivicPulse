"""
CivicPulse — ML Scheduler

Runs CSS computation every hour and anomaly detection every 4 hours.
Writes results to css_history table and Redis cache.

Key behaviors:
- Never crashes on individual ward failure — catch, log, continue
- Logs every run with ward count, duration, and failures
- CSS results cached in Redis with configurable TTL
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import psycopg2
import redis

from feature_engineering import build_feature_vector, get_feature_names, SIGNAL_TYPES
from fusion_model import CSSFusionModel
from anomaly_detector import AnomalyDetector

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("civicpulse.ml.scheduler")

# Environment validation
DATABASE_URL = os.environ.get("DATABASE_URL")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_CSS_TTL = int(os.environ.get("REDIS_CSS_TTL_SECONDS", "3600"))
CSS_HIGH_THRESHOLD = int(os.environ.get("CSS_HIGH_THRESHOLD", "56"))
CSS_CRITICAL_THRESHOLD = int(os.environ.get("CSS_CRITICAL_THRESHOLD", "76"))


def get_db_connection():
    """Create database connection with validation."""
    if not DATABASE_URL:
        raise EnvironmentError("DATABASE_URL is required")
    try:
        return psycopg2.connect(DATABASE_URL)
    except psycopg2.Error as e:
        logger.error("Database connection failed: %s", e)
        raise


def get_redis_connection():
    """Create Redis connection with error handling."""
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        return r
    except redis.RedisError as e:
        logger.warning("Redis connection failed: %s — CSS caching disabled", e)
        return None


def fetch_wards(conn) -> list[dict]:
    """Fetch all active wards from database."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, city_id, ward_code, ward_label, lat, lng FROM wards")
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except psycopg2.Error as e:
        logger.error("Failed to fetch wards: %s", e)
        return []


def fetch_ward_signals(conn, ward_id: str, days: int = 7) -> pd.DataFrame:
    """Fetch recent signals for a ward."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT signal_type, intensity_score, confidence, signal_timestamp
                FROM signals
                WHERE ward_id = %s AND signal_timestamp >= %s
                ORDER BY signal_timestamp DESC
                """,
                (ward_id, cutoff),
            )
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            if not rows:
                return pd.DataFrame(columns=columns)
            df = pd.DataFrame(rows, columns=columns)
            df["signal_timestamp"] = pd.to_datetime(df["signal_timestamp"], utc=True)
            return df
    except psycopg2.Error as e:
        logger.error("Failed to fetch signals for ward %s: %s", ward_id, e)
        return pd.DataFrame()


def fetch_css_history(conn, ward_id: str, days: int = 30) -> pd.DataFrame:
    """Fetch CSS history for a ward."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT css_score, computed_at
                FROM css_history
                WHERE ward_id = %s AND computed_at >= %s
                ORDER BY computed_at DESC
                """,
                (ward_id, cutoff),
            )
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            if not rows:
                return pd.DataFrame(columns=columns)
            df = pd.DataFrame(rows, columns=columns)
            df["computed_at"] = pd.to_datetime(df["computed_at"], utc=True)
            return df
    except psycopg2.Error as e:
        logger.error("Failed to fetch CSS history for ward %s: %s", ward_id, e)
        return pd.DataFrame()


def count_data_days(conn, ward_id: str) -> int:
    """Count how many days of signal data exist for a ward."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXTRACT(DAY FROM (MAX(signal_timestamp) - MIN(signal_timestamp)))
                FROM signals WHERE ward_id = %s
                """,
                (ward_id,),
            )
            row = cur.fetchone()
            return int(row[0]) if row and row[0] else 0
    except psycopg2.Error as e:
        logger.error("Failed to count data days for ward %s: %s", ward_id, e)
        return 0


def write_css_result(conn, ward_id: str, css_score: float, contributing: dict) -> None:
    """Write CSS result to css_history table."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO css_history (ward_id, css_score, contributing_signals, computed_at)
                VALUES (%s, %s, %s, %s)
                """,
                (ward_id, css_score, json.dumps(contributing), datetime.now(timezone.utc)),
            )
            conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        logger.error("Failed to write CSS for ward %s: %s", ward_id, e)


def write_anomaly_result(conn, ward_id: str, result: dict) -> None:
    """Write anomaly detection result to anomalies table."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO anomalies (ward_id, severity, is_anomaly, triggering_signals, detected_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    ward_id,
                    result["severity"],
                    result["anomaly"],
                    json.dumps(result.get("triggering_signals", [])),
                    datetime.now(timezone.utc),
                ),
            )
            conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        logger.error("Failed to write anomaly for ward %s: %s", ward_id, e)


def cache_css_to_redis(redis_conn, ward_id: str, css_score: float) -> None:
    """Cache latest CSS score in Redis."""
    if redis_conn is None:
        return
    try:
        redis_conn.setex(
            f"css:ward:{ward_id}",
            REDIS_CSS_TTL,
            json.dumps({"css_score": css_score, "updated_at": datetime.now(timezone.utc).isoformat()}),
        )
    except redis.RedisError as e:
        logger.warning("Failed to cache CSS for ward %s: %s", ward_id, e)


def run_css_cycle(conn, redis_conn, css_model: CSSFusionModel) -> dict:
    """Run CSS computation for all wards."""
    cycle_start = time.time()
    wards = fetch_wards(conn)
    success_count = 0
    failure_count = 0
    results = {}

    for ward in wards:
        ward_id = str(ward["id"])
        try:
            signals_df = fetch_ward_signals(conn, ward_id)
            css_history_df = fetch_css_history(conn, ward_id)
            data_days = count_data_days(conn, ward_id)

            # Build features (use empty neighbor list for now)
            features = build_feature_vector(
                ward_id, signals_df, css_history_df, neighbor_css_scores=[], now=None
            )

            # Predict CSS
            prediction = css_model.predict(features, data_days)

            if prediction.get("css") is not None:
                css_score = prediction["css"]
                write_css_result(conn, ward_id, css_score, features)
                cache_css_to_redis(redis_conn, ward_id, css_score)
                results[ward_id] = css_score
                success_count += 1
            else:
                logger.warning(
                    "CSS prediction skipped for ward %s: %s",
                    ward_id, prediction.get("error"),
                )
                failure_count += 1

        except Exception as e:
            # Never crash on individual ward failure
            logger.error("CSS computation failed for ward %s: %s", ward_id, e, exc_info=True)
            failure_count += 1

    duration = time.time() - cycle_start
    logger.info(
        "CSS cycle complete: %d wards, %d success, %d failures, %.1fs duration",
        len(wards), success_count, failure_count, duration,
    )

    return {
        "wards_total": len(wards),
        "success": success_count,
        "failures": failure_count,
        "duration_seconds": round(duration, 2),
    }


def run_anomaly_cycle(conn, anomaly_model: AnomalyDetector) -> dict:
    """Run anomaly detection for all wards."""
    cycle_start = time.time()
    wards = fetch_wards(conn)
    anomalies_found = 0

    for ward in wards:
        ward_id = str(ward["id"])
        try:
            signals_df = fetch_ward_signals(conn, ward_id, days=1)
            css_history_df = fetch_css_history(conn, ward_id)

            features = build_feature_vector(
                ward_id, signals_df, css_history_df, neighbor_css_scores=[], now=None
            )

            result = anomaly_model.detect(ward_id, features)
            write_anomaly_result(conn, ward_id, result)

            if result.get("anomaly"):
                anomalies_found += 1

        except Exception as e:
            logger.error("Anomaly detection failed for ward %s: %s", ward_id, e)

    duration = time.time() - cycle_start
    logger.info(
        "Anomaly cycle complete: %d wards checked, %d anomalies, %.1fs",
        len(wards), anomalies_found, duration,
    )

    return {"wards_checked": len(wards), "anomalies_found": anomalies_found}


def main():
    parser = argparse.ArgumentParser(description="CivicPulse ML Scheduler")
    parser.add_argument("--interval", type=int, default=3600, help="CSS cycle interval in seconds")
    parser.add_argument("--anomaly-interval", type=int, default=14400, help="Anomaly cycle interval (default: 4h)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    # Validate env
    if not DATABASE_URL:
        logger.error("DATABASE_URL is required")
        sys.exit(1)

    conn = get_db_connection()
    redis_conn = get_redis_connection()

    # Initialize models
    css_model = CSSFusionModel()
    anomaly_model = AnomalyDetector()

    # Try to load existing models
    try:
        css_model.load()
        logger.info("Loaded existing CSS model")
    except FileNotFoundError:
        logger.warning("No pre-trained CSS model found — predictions will be skipped until model is trained")

    try:
        anomaly_model.load()
        logger.info("Loaded existing anomaly model")
    except FileNotFoundError:
        logger.warning("No pre-trained anomaly model found — anomaly detection will be skipped")

    if args.once:
        run_css_cycle(conn, redis_conn, css_model)
        run_anomaly_cycle(conn, anomaly_model)
        conn.close()
        return

    # Main scheduler loop
    last_css_run = 0
    last_anomaly_run = 0

    logger.info(
        "ML Scheduler started: CSS every %ds, Anomaly every %ds",
        args.interval, args.anomaly_interval,
    )

    try:
        while True:
            now = time.time()

            if now - last_css_run >= args.interval:
                try:
                    run_css_cycle(conn, redis_conn, css_model)
                    last_css_run = now
                except Exception as e:
                    logger.error("CSS cycle error: %s", e, exc_info=True)

            if now - last_anomaly_run >= args.anomaly_interval:
                try:
                    run_anomaly_cycle(conn, anomaly_model)
                    last_anomaly_run = now
                except Exception as e:
                    logger.error("Anomaly cycle error: %s", e, exc_info=True)

            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
    finally:
        conn.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    main()
