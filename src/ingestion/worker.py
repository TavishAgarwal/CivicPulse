"""
CivicPulse — Ingestion Worker

Main entry point for the signal ingestion service.
Fetches signals from all registered connectors, anonymizes them,
and writes to the database.

Usage:
    python worker.py --use-mocks    # Development mode (default)
    python worker.py                # Production mode
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import execute_values

from anonymizer import anonymize_at_source, validate_no_pii
from registry import get_all_connectors, list_registered_types

# Import connectors to trigger registration
import connectors.pharmacy
import connectors.school
import connectors.utility
import connectors.social
import connectors.foodbank
import connectors.health

# Import mocks to trigger registration
import mocks.pharmacy_mock
import mocks.school_mock
import mocks.utility_mock
import mocks.social_mock
import mocks.foodbank_mock
import mocks.health_mock

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("civicpulse.ingestion")


def get_db_connection():
    """Create a database connection with error handling."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise EnvironmentError(
            "DATABASE_URL environment variable is required. "
            "Example: postgresql://civicpulse:password@localhost:5432/civicpulse_dev"
        )
    try:
        conn = psycopg2.connect(database_url)
        logger.info("Database connection established")
        return conn
    except psycopg2.Error as e:
        logger.error("Failed to connect to database: %s", e)
        raise


def resolve_ward_id(conn, location_pin: str) -> str | None:
    """Resolve a location_pin to a ward UUID."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM wards WHERE ward_code = %s LIMIT 1",
                (location_pin,),
            )
            row = cur.fetchone()
            return str(row[0]) if row else None
    except psycopg2.Error as e:
        logger.error("Failed to resolve ward for %s: %s", location_pin, e)
        return None


def write_signal_to_db(conn, signal_data: dict, ward_id: str) -> None:
    """Write an anonymized signal to the database."""
    try:
        # Final PII safety check before writing
        if not validate_no_pii(signal_data):
            logger.error("PII detected in signal — refusing to write to database!")
            return

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO signals (ward_id, source, signal_type, intensity_score,
                                     confidence, signal_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    ward_id,
                    signal_data["source"],
                    signal_data["signal_type"],
                    signal_data["intensity_score"],
                    signal_data["confidence"],
                    signal_data["timestamp"],
                ),
            )
            signal_id = cur.fetchone()[0]
            conn.commit()
            logger.debug("Wrote signal %s (type=%s, ward=%s)", signal_id, signal_data["signal_type"], ward_id)
    except psycopg2.Error as e:
        conn.rollback()
        logger.error("Failed to write signal to DB: %s", e)


async def run_connector(connector, conn) -> int:
    """Run a single connector and write its signals to the database."""
    count = 0
    try:
        async for signal in connector.fetch():
            signal_dict = signal.model_dump()

            # Anonymize (should already be done in connector, but double-check)
            anonymized = anonymize_at_source(signal_dict)

            # Resolve ward
            ward_id = resolve_ward_id(conn, anonymized["location_pin"])
            if not ward_id:
                logger.warning(
                    "Unknown ward for location_pin=%s, skipping signal",
                    anonymized["location_pin"],
                )
                continue

            write_signal_to_db(conn, anonymized, ward_id)
            count += 1

    except Exception as e:
        logger.error(
            "Error in connector %s: %s", connector.source_name, e,
            exc_info=True,
        )

    return count


async def ingestion_loop(conn, interval_seconds: int = 300) -> None:
    """Main ingestion loop — runs all connectors on a schedule."""
    logger.info("Starting ingestion loop (interval=%ds)", interval_seconds)

    registered = list_registered_types()
    env = os.environ.get("CIVICPULSE_ENV", "development")
    mode = "mock" if env == "development" else "real"
    logger.info("Environment: %s, Mode: %s", env, mode)
    logger.info("Registered connectors: %s", registered)

    while True:
        cycle_start = datetime.now(timezone.utc)
        total_signals = 0

        connectors = get_all_connectors()
        if not connectors:
            logger.warning("No connectors available. Waiting for next cycle...")
        else:
            for connector in connectors:
                try:
                    count = await run_connector(connector, conn)
                    total_signals += count
                    logger.info(
                        "Connector %s: ingested %d signals",
                        connector.source_name, count,
                    )
                except Exception as e:
                    # Never crash on individual connector failure
                    logger.error(
                        "Connector %s failed: %s", connector.source_name, e,
                        exc_info=True,
                    )

        duration = (datetime.now(timezone.utc) - cycle_start).total_seconds()
        logger.info(
            "Ingestion cycle complete: %d signals in %.1fs. Next cycle in %ds.",
            total_signals, duration, interval_seconds,
        )

        await asyncio.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(description="CivicPulse Signal Ingestion Worker")
    parser.add_argument(
        "--use-mocks", action="store_true",
        help="Force mock connectors (sets CIVICPULSE_ENV=development)",
    )
    parser.add_argument(
        "--interval", type=int, default=300,
        help="Seconds between ingestion cycles (default: 300)",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Run one ingestion cycle and exit",
    )
    args = parser.parse_args()

    if args.use_mocks:
        os.environ["CIVICPULSE_ENV"] = "development"

    # Validate required env vars
    required_vars = ["DATABASE_URL"]
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        logger.error("Missing required environment variables: %s", missing)
        sys.exit(1)

    conn = get_db_connection()

    try:
        if args.once:
            asyncio.run(run_once(conn))
        else:
            asyncio.run(ingestion_loop(conn, args.interval))
    except KeyboardInterrupt:
        logger.info("Ingestion worker stopped by user")
    finally:
        conn.close()
        logger.info("Database connection closed")


async def run_once(conn):
    """Run a single ingestion cycle."""
    connectors = get_all_connectors()
    total = 0
    for connector in connectors:
        try:
            count = await run_connector(connector, conn)
            total += count
        except Exception as e:
            logger.error("Connector %s failed: %s", connector.source_name, e)
    logger.info("Single cycle complete: %d signals ingested", total)


if __name__ == "__main__":
    main()
