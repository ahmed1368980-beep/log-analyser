import logging

import psycopg2
from psycopg2.extras import execute_values

from config.settings import DB_CONFIG

logger = logging.getLogger(__name__)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS auth_events (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    service VARCHAR(50),
    event_type VARCHAR(10) NOT NULL,      -- FAILED ou SUCCESS
    username VARCHAR(255),
    ip_address VARCHAR(45),
    country VARCHAR(10),
    is_invalid_user BOOLEAN NOT NULL DEFAULT FALSE
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_type_country ON auth_events (event_type, country);",
    "CREATE INDEX IF NOT EXISTS idx_type_user ON auth_events (event_type, username);",
    "CREATE INDEX IF NOT EXISTS idx_type_invalid ON auth_events (event_type, is_invalid_user);",
]

INSERT = """
INSERT INTO auth_events
    (event_date, event_time, service, event_type, username, ip_address, country, is_invalid_user)
VALUES %s
"""

# --- Les 3 requêtes du dashboard ---
Q_FAILED_BY_COUNTRY = """
SELECT COALESCE(country, 'UNKNOWN') AS country, COUNT(*) AS total
FROM auth_events
WHERE event_type = 'FAILED'
GROUP BY country
ORDER BY total DESC
LIMIT 10;
"""

Q_SUCCESS_BY_USER = """
SELECT username, COUNT(*) AS total
FROM auth_events
WHERE event_type = 'SUCCESS'
GROUP BY username
ORDER BY total DESC
LIMIT 10;
"""

Q_FAILED_INVALID_USER = """
SELECT username, COUNT(*) AS total
FROM auth_events
WHERE event_type = 'FAILED' AND is_invalid_user = TRUE
GROUP BY username
ORDER BY total DESC
LIMIT 10;
"""


def get_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connexion PostgreSQL OK (%s)", DB_CONFIG["dbname"])
        return conn
    except psycopg2.Error:
        logger.exception("Connexion PostgreSQL impossible")
        raise


def create_table(conn):
    """Crée la table et les index, et la vide (pour ne pas avoir de doublons si on relance)."""
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE)
            for sql in CREATE_INDEXES:
                cur.execute(sql)
            cur.execute("TRUNCATE TABLE auth_events RESTART IDENTITY;")
        conn.commit()
        logger.info("Table auth_events prête (index créés, table vidée)")
    except psycopg2.Error:
        conn.rollback()
        logger.exception("Erreur à la création de la table")
        raise


def insert_events(conn, rows, batch_size=1000):
    """rows = liste de tuples dans l'ordre des colonnes de INSERT."""
    if not rows:
        logger.warning("Aucune ligne à insérer")
        return 0
    try:
        with conn.cursor() as cur:
            execute_values(cur, INSERT, rows, page_size=batch_size)
        conn.commit()
        logger.info("%d lignes insérées", len(rows))
        return len(rows)
    except psycopg2.Error:
        conn.rollback()
        logger.exception("Erreur à l'insertion")
        raise


def _run_query(conn, sql, name):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    except psycopg2.Error:
        conn.rollback()
        logger.exception("Erreur sur la requête %s", name)
        return []


def failed_by_country(conn):
    return _run_query(conn, Q_FAILED_BY_COUNTRY, "failed_by_country")


def success_by_user(conn):
    return _run_query(conn, Q_SUCCESS_BY_USER, "success_by_user")


def failed_invalid_user(conn):
    return _run_query(conn, Q_FAILED_INVALID_USER, "failed_invalid_user")