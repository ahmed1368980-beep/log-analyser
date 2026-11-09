import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"
IP_CACHE_FILE = DATA_DIR / "ip_cache.json"
LOG_FILE = BASE_DIR / "app.log"

# Les auth.log n'ont pas l'année dans la date ("Nov  9 10:12:01")
LOG_YEAR = datetime.now().year

# Token IPinfo et mot de passe BD : lus dans les variables d'environnement
# (on ne met JAMAIS un secret dans le code poussé sur Git)
IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "auth_logs"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}