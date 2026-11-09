import ipaddress
import json
import logging

import requests

from config.settings import IP_CACHE_FILE, IPINFO_TOKEN

logger = logging.getLogger(__name__)

IPINFO_URL = "https://ipinfo.io/{ip}/json"
SAVE_EVERY = 100  # sauvegarde du cache tous les 100 nouveaux appels


class QuotaExceeded(Exception):
    pass


def load_cache(path=IP_CACHE_FILE):
    try:
        with open(path, "r", encoding="utf-8") as f:
            cache = json.load(f)
        logger.info("Cache IP chargé : %d entrées", len(cache))
        return cache
    except FileNotFoundError:
        logger.info("Pas de cache IP, on part de zéro")
        return {}
    except (json.JSONDecodeError, OSError):
        logger.exception("Cache IP illisible, on repart de zéro")
        return {}


def save_cache(cache, path=IP_CACHE_FILE):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except OSError:
        logger.exception("Impossible d'écrire le cache IP")


def is_private(ip):
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return True  # IP mal formée : on ne l'envoie pas à l'API


def fetch_country(ip):
    """Appelle IPinfo. Renvoie le code pays, ou None si l'appel a échoué."""
    params = {"token": IPINFO_TOKEN} if IPINFO_TOKEN else {}
    try:
        r = requests.get(IPINFO_URL.format(ip=ip), params=params, timeout=5)
        if r.status_code == 429:
            raise QuotaExceeded()
        r.raise_for_status()
        data = r.json()
        if data.get("bogon"):
            return "LOCAL"
        return data.get("country", "UNKNOWN")
    except QuotaExceeded:
        raise
    except requests.RequestException:
        logger.exception("Appel IPinfo échoué pour %s", ip)
        return None
    except ValueError:
        logger.error("Réponse IPinfo non valide pour %s", ip)
        return None


def get_countries(ips):
    """Prend une liste d'IP uniques, renvoie un dict {ip: pays}."""
    if not IPINFO_TOKEN:
        logger.warning("IPINFO_TOKEN absent : quota très limité sans token")

    cache = load_cache()
    result = {}
    new_calls = 0
    quota_ok = True

    try:
        for ip in ips:
            if ip in cache:
                result[ip] = cache[ip]
            elif is_private(ip):
                result[ip] = "LOCAL"
            elif not quota_ok:
                result[ip] = "UNKNOWN"
            else:
                try:
                    country = fetch_country(ip)
                except QuotaExceeded:
                    logger.error("Quota IPinfo dépassé : le reste sera UNKNOWN")
                    quota_ok = False
                    result[ip] = "UNKNOWN"
                    continue
                if country is None:          # erreur réseau : on ne met pas en cache
                    result[ip] = "UNKNOWN"
                else:
                    cache[ip] = country
                    result[ip] = country
                    new_calls += 1
                    if new_calls % SAVE_EVERY == 0:
                        save_cache(cache)
    finally:
        save_cache(cache)

    logger.info("Géolocalisation terminée : %d IP, %d nouveaux appels API", len(result), new_calls)
    return result