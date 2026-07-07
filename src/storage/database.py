import sqlite3
import logging
import os

from config import settings

logger = logging.getLogger(__name__)


def get_connection():
    os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {settings.DATABASE_TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at TEXT NOT NULL,
                heartRate REAL NOT NULL,
                respiratoryRate REAL,
                status TEXT,
                health_score REAL,
                risk_level TEXT
            )
        """)
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_received_at
            ON {settings.DATABASE_TABLE_NAME} (received_at)
        """)
        conn.commit()
        logger.info(f"Database initialized at {settings.DATABASE_PATH}, table '{settings.DATABASE_TABLE_NAME}' ready.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    init_db()
    print(f"Database ready at: {settings.DATABASE_PATH}")