import logging
import os
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    host = os.getenv("POSTGRES_HOST", "db")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    database = os.getenv("POSTGRES_DB", "llm_app")
    user = os.getenv("POSTGRES_USER", "llm_user")
    password = os.getenv("POSTGRES_PASSWORD", "llm_password")

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=database,
        user=user,
        password=password,
        cursor_factory=RealDictCursor,
    )


def init_db(logger: Optional[logging.Logger] = None) -> None:
    try:
        conn = get_db_connection()
    except Exception as exc:  # noqa: BLE001
        if logger:
            logger.warning("Could not connect to Postgres on startup: %s", exc)
        return

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS llm_requests (
                        id SERIAL PRIMARY KEY,
                        prompt TEXT NOT NULL,
                        response TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )
    finally:
        conn.close()


def save_llm_request(prompt: str, response: str, logger: Optional[logging.Logger] = None) -> None:
    try:
        conn = get_db_connection()
    except Exception as exc:  # noqa: BLE001
        if logger:
            logger.warning("Could not connect to Postgres to save LLM request: %s", exc)
        return

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO llm_requests (prompt, response)
                    VALUES (%s, %s);
                    """,
                    (prompt, response),
                )
    finally:
        conn.close()

