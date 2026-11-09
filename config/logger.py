import logging
from logging.handlers import RotatingFileHandler

from config.settings import LOG_FILE

LOG_FORMAT = "%(asctime)s|%(levelname)s|%(name)s|%(message)s"


def setup_logging():
    """À appeler une seule fois, au début de main.py."""
    root = logging.getLogger()
    if root.handlers:      # déjà configuré
        return
    root.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Affichage console en plus, pour suivre le programme pendant qu'il tourne
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)