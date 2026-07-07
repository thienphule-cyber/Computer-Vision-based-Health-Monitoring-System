import logging

from config import settings
from storage.database import get_connection

logger = logging.getLogger(__name__)


def save_record(record: dict) -> int:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {settings.DATABASE_TABLE_NAME}
                (received_at, heartRate, respiratoryRate, status, health_score, risk_level)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            record.get("received_at"),
            record.get("heartRate"),
            record.get("respiratoryRate"),
            record.get("status"),
            record.get("health_score"),
            record.get("risk_level"),
        ))
        conn.commit()
        new_id = cursor.lastrowid
        logger.debug(f"Record saved with id={new_id}: {record}")
        return new_id
    except Exception as e:
        logger.error(f"Failed to save record: {e}. Record: {record}")
        raise
    finally:
        conn.close()


def update_record_analytics(record_id: int, health_score: float, risk_level: str, status: str = None) -> None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if status is not None:
            cursor.execute(f"""
                UPDATE {settings.DATABASE_TABLE_NAME}
                SET health_score = ?, risk_level = ?, status = ?
                WHERE id = ?
            """, (health_score, risk_level, status, record_id))
        else:
            cursor.execute(f"""
                UPDATE {settings.DATABASE_TABLE_NAME}
                SET health_score = ?, risk_level = ?
                WHERE id = ?
            """, (health_score, risk_level, record_id))
        conn.commit()
        logger.debug(f"Record id={record_id} updated with health_score={health_score}, risk_level={risk_level}")
    except Exception as e:
        logger.error(f"Failed to update record id={record_id}: {e}")
        raise
    finally:
        conn.close()


def get_latest_records(limit: int = None) -> list:
    if limit is None:
        limit = settings.TREND_WINDOW_SIZE

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM {settings.DATABASE_TABLE_NAME}
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        records = [dict(row) for row in rows]
        records.reverse()
        return records
    except Exception as e:
        logger.error(f"Failed to fetch latest records: {e}")
        raise
    finally:
        conn.close()


def get_records_by_time_range(start_time: str, end_time: str) -> list:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM {settings.DATABASE_TABLE_NAME}
            WHERE received_at BETWEEN ? AND ?
            ORDER BY received_at ASC
        """, (start_time, end_time))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch records by time range: {e}")
        raise
    finally:
        conn.close()


def get_record_count() -> int:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) as count FROM {settings.DATABASE_TABLE_NAME}")
        return cursor.fetchone()["count"]
    finally:
        conn.close()
