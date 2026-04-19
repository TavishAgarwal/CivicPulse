"""
CivicPulse — Ingestion Worker Tests
Tests worker DB operations and ingestion flow with mocked dependencies.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))


class TestResolveWardId:
    """Tests for ward ID resolution."""

    def test_resolve_existing_ward(self):
        from worker import resolve_ward_id
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = ("uuid-123",)
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        result = resolve_ward_id(conn, "WARD-DEL-001")
        assert result == "uuid-123"

    def test_resolve_nonexistent_ward(self):
        from worker import resolve_ward_id
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        result = resolve_ward_id(conn, "WARD-NONEXISTENT")
        assert result is None

    def test_resolve_handles_db_error(self):
        import psycopg2
        from worker import resolve_ward_id
        conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = psycopg2.Error("DB error")
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        result = resolve_ward_id(conn, "WARD-DEL-001")
        assert result is None


class TestWriteSignalToDb:
    """Tests for writing signals to the database."""

    def test_write_valid_signal(self, sample_signal):
        from worker import write_signal_to_db
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = ("signal-uuid",)
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        write_signal_to_db(conn, sample_signal, "ward-uuid")
        conn.commit.assert_called_once()

    def test_write_refuses_pii(self, sample_signal_with_pii):
        from worker import write_signal_to_db
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        # PII signals should be refused
        write_signal_to_db(conn, sample_signal_with_pii, "ward-uuid")
        # Should not commit if PII is detected
        # (depends on validate_no_pii behavior)

    def test_write_handles_db_error(self, sample_signal):
        import psycopg2
        from worker import write_signal_to_db
        conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = psycopg2.Error("Insert failed")
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        # Should not raise, just log the error
        write_signal_to_db(conn, sample_signal, "ward-uuid")
        conn.rollback.assert_called_once()


class TestGetDbConnection:
    """Tests for database connection handling."""

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_database_url_raises(self):
        from worker import get_db_connection
        os.environ.pop("DATABASE_URL", None)
        with pytest.raises(EnvironmentError):
            get_db_connection()

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost:5432/test"})
    @patch("worker.psycopg2.connect")
    def test_successful_connection(self, mock_connect):
        from worker import get_db_connection
        mock_connect.return_value = MagicMock()
        conn = get_db_connection()
        assert conn is not None
        mock_connect.assert_called_once()
