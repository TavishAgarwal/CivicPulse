"""
CivicPulse — Dispatch Engine

Main dispatch service that monitors CSS scores and triggers volunteer matching.
Runs as a background service, polling CSS scores and auto-creating dispatches
when thresholds are crossed.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import psycopg2
import redis as redis_lib

from thresholds import (
    requires_dispatch, requires_human_approval, can_auto_dispatch,
    get_status_label, CSS_HIGH_THRESHOLD,
)
from matcher import rank_volunteers

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("civicpulse.dispatch")

DATABASE_URL = os.environ.get("DATABASE_URL")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
FATIGUE_INCREMENT = float(os.environ.get("FATIGUE_INCREMENT_PER_DISPATCH", "0.15"))
FATIGUE_RECOVERY_DAYS = int(os.environ.get("FATIGUE_RECOVERY_DAYS", "2"))


def get_db():
    if not DATABASE_URL:
        raise EnvironmentError("DATABASE_URL is required")
    return psycopg2.connect(DATABASE_URL)


def get_redis():
    try:
        r = redis_lib.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        return r
    except Exception as e:
        logger.warning("Redis not available: %s", e)
        return None


def fetch_high_stress_wards(conn) -> list[dict]:
    """Fetch wards with CSS >= high threshold."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT ON (ch.ward_id)
                ch.ward_id, w.name, w.city_id, w.lat, w.lng, ch.css_score
            FROM css_history ch
            JOIN wards w ON w.id = ch.ward_id
            WHERE ch.css_score >= %s
            ORDER BY ch.ward_id, ch.computed_at DESC
            """,
            (CSS_HIGH_THRESHOLD,),
        )
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def fetch_available_volunteers(conn, city_id: str) -> list[dict]:
    """Fetch available volunteers for a city."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, display_handle, skills, max_radius_km, lat, lng,
                   city_id, fatigue_score, is_available
            FROM volunteers
            WHERE is_available = TRUE AND fatigue_score < 0.85
            AND (city_id = %s OR city_id IS NULL)
            """,
            (city_id,),
        )
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
        result = []
        for row in rows:
            d = dict(zip(columns, row))
            d["id"] = str(d["id"])
            d["fatigue_score"] = float(d.get("fatigue_score", 0))
            d["lat"] = float(d["lat"]) if d.get("lat") else None
            d["lng"] = float(d["lng"]) if d.get("lng") else None
            result.append(d)
        return result


def has_active_dispatch(conn, ward_id: str) -> bool:
    """Check if ward already has an active dispatch."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM dispatches WHERE ward_id = %s AND status IN ('pending', 'confirmed', 'active')",
            (ward_id,),
        )
        return cur.fetchone()[0] > 0


def create_dispatch(conn, ward_id: str, volunteer_id: str, css_score: float, match_score: float) -> str:
    """Create a new dispatch record."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO dispatches (ward_id, volunteer_id, css_at_dispatch, status, match_score, dispatched_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (ward_id, volunteer_id, css_score,
             "active" if can_auto_dispatch(css_score) else "pending",
             match_score, datetime.now(timezone.utc)),
        )
        dispatch_id = str(cur.fetchone()[0])
        conn.commit()
        return dispatch_id


def apply_fatigue_recovery(conn) -> int:
    """Apply daily fatigue recovery to all volunteers."""
    recovery_rate = 1.0 / max(1, FATIGUE_RECOVERY_DAYS)
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE volunteers
            SET fatigue_score = GREATEST(0, fatigue_score - %s),
                updated_at = NOW()
            WHERE fatigue_score > 0
            """,
            (recovery_rate,),
        )
        count = cur.rowcount
        conn.commit()
        return count


def dispatch_cycle(conn) -> dict:
    """Run one dispatch evaluation cycle."""
    cycle_start = time.time()
    wards = fetch_high_stress_wards(conn)
    dispatches_created = 0
    skipped = 0

    for ward in wards:
        ward_id = str(ward["ward_id"])
        css_score = float(ward["css_score"])

        try:
            # Skip if already dispatched
            if has_active_dispatch(conn, ward_id):
                skipped += 1
                continue

            if not requires_dispatch(css_score):
                continue

            # Find volunteers
            volunteers = fetch_available_volunteers(conn, ward.get("city_id", ""))
            if not volunteers:
                logger.warning("No available volunteers for ward %s (%s)", ward["name"], ward_id)
                continue

            ward_dict = {
                "lat": float(ward["lat"]) if ward.get("lat") else None,
                "lng": float(ward["lng"]) if ward.get("lng") else None,
            }
            ranked = rank_volunteers(volunteers, ward_dict, [], top_n=1)

            if not ranked:
                logger.warning("No suitable matches for ward %s", ward["name"])
                continue

            best = ranked[0]
            vol_id = best["volunteer"]["id"]
            match_score = best["scores"]["total"]

            if can_auto_dispatch(css_score):
                dispatch_id = create_dispatch(conn, ward_id, vol_id, css_score, match_score)
                logger.info(
                    "🔴 AUTO-DISPATCH: ward=%s css=%.1f volunteer=%s dispatch=%s",
                    ward["name"], css_score, vol_id, dispatch_id,
                )
                dispatches_created += 1
            elif requires_human_approval(css_score):
                dispatch_id = create_dispatch(conn, ward_id, vol_id, css_score, match_score)
                logger.info(
                    "🟠 PENDING APPROVAL: ward=%s css=%.1f volunteer=%s dispatch=%s",
                    ward["name"], css_score, vol_id, dispatch_id,
                )
                dispatches_created += 1

        except Exception as e:
            logger.error("Dispatch error for ward %s: %s", ward_id, e, exc_info=True)

    duration = time.time() - cycle_start
    logger.info(
        "Dispatch cycle: %d wards checked, %d dispatches created, %d skipped, %.1fs",
        len(wards), dispatches_created, skipped, duration,
    )
    return {"wards": len(wards), "dispatched": dispatches_created, "skipped": skipped}


def main():
    parser = argparse.ArgumentParser(description="CivicPulse Dispatch Engine")
    parser.add_argument("--interval", type=int, default=300, help="Check interval seconds")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    if not DATABASE_URL:
        logger.error("DATABASE_URL required")
        sys.exit(1)

    conn = get_db()
    logger.info("Dispatch engine started (interval=%ds)", args.interval)

    try:
        if args.once:
            dispatch_cycle(conn)
            return

        last_recovery = time.time()
        while True:
            try:
                dispatch_cycle(conn)
            except Exception as e:
                logger.error("Dispatch cycle error: %s", e, exc_info=True)

            # Apply fatigue recovery once per day
            if time.time() - last_recovery > 86400:
                count = apply_fatigue_recovery(conn)
                logger.info("Fatigue recovery applied to %d volunteers", count)
                last_recovery = time.time()

            time.sleep(args.interval)

    except KeyboardInterrupt:
        logger.info("Dispatch engine stopped")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
