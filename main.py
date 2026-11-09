import logging
import sys

from config.logger import setup_logging

setup_logging()   # avant les autres imports de modules

from config.settings import DATA_DIR, LOG_YEAR
from Ingestion.raw import list_log_files, read_log_file
from Process.exctract_transform import parse_line
from Process.geolocation import get_countries
from Storage import database
from Serving.visualizer import show_dashboard

logger = logging.getLogger("main")


def main():
    logger.info("=== Démarrage du pipeline ===")

    # 1. Ingestion + 2. Parsing
    events = []
    total_lines = 0
    for path in list_log_files(DATA_DIR):
        for line in read_log_file(path):
            total_lines += 1
            event = parse_line(line, LOG_YEAR)
            if event:
                events.append(event)
    logger.info("%d lignes lues, %d événements retenus", total_lines, len(events))

    if not events:
        logger.error("Aucun événement trouvé, arrêt du pipeline")
        return 1

    # 3. Géolocalisation (une seule fois par IP unique)
    unique_ips = sorted({e["ip"] for e in events})
    countries = get_countries(unique_ips)

    rows = [
        (e["date"], e["time"], e["service"], e["event"], e["user"],
         e["ip"], countries.get(e["ip"], "UNKNOWN"), e["invalid_user"])
        for e in events
    ]

    # 4. Stockage + requêtes
    conn = database.get_connection()
    try:
        database.create_table(conn)
        database.insert_events(conn, rows)
        failed_country = database.failed_by_country(conn)
        success_user = database.success_by_user(conn)
        failed_invalid = database.failed_invalid_user(conn)
    finally:
        conn.close()

    # 5. Dashboard
    show_dashboard(failed_country, success_user, failed_invalid)
    logger.info("=== Pipeline terminé ===")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logger.exception("Le pipeline a planté")
        sys.exit(1)
        