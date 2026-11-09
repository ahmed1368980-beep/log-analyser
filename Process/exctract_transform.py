import logging
import re
from datetime import date, datetime

logger = logging.getLogger(__name__)

MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
          "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

# Format classique : "Nov  9 10:12:01 host sshd[123]: message"
SYSLOG_LINE = re.compile(
    r"^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})"
    r"\s+\S+\s+(?P<service>[^\s\[:]+)(?:\[\d+\])?:\s+(?P<message>.*)$"
)

# Format ISO : "2026-11-09T10:12:01.123+00:00 host sshd[123]: message"
ISO_LINE = re.compile(
    r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T(?P<time>\d{2}:\d{2}:\d{2})\S*"
    r"\s+\S+\s+(?P<service>[^\s\[:]+)(?:\[\d+\])?:\s+(?P<message>.*)$"
)

IP = r"[0-9a-fA-F:.]+"  # IPv4 ou IPv6

FAILED = re.compile(
    rf"Failed (?:password|publickey) for (?P<invalid>invalid user )?(?P<user>\S+) "
    rf"from (?P<ip>{IP}) port \d+"
)
ACCEPTED = re.compile(
    rf"Accepted (?:password|publickey|keyboard-interactive/pam) for (?P<user>\S+) "
    rf"from (?P<ip>{IP}) port \d+"
)


def _build_date(year, month, day):
    """Construit la date. Si elle est dans le futur, c'est que le log date de l'année d'avant."""
    d = date(year, month, day)
    if d > date.today():
        d = date(year - 1, month, day)
    return d


def parse_line(line, default_year):
    """Transforme une ligne en dictionnaire, ou None si elle ne nous intéresse pas."""
    try:
        m = SYSLOG_LINE.match(line)
        if m:
            month = MONTHS.get(m["month"])
            if month is None:
                return None
            event_date = _build_date(default_year, month, int(m["day"]))
        else:
            m = ISO_LINE.match(line)
            if not m:
                return None
            event_date = date(int(m["year"]), int(m["month"]), int(m["day"]))

        event_time = datetime.strptime(m["time"], "%H:%M:%S").time()
        service = m["service"]
        message = m["message"]

        f = FAILED.search(message)
        if f:
            return {"date": event_date, "time": event_time, "service": service,
                    "event": "FAILED", "user": f["user"], "ip": f["ip"],
                    "invalid_user": f["invalid"] is not None}

        a = ACCEPTED.search(message)
        if a:
            return {"date": event_date, "time": event_time, "service": service,
                    "event": "SUCCESS", "user": a["user"], "ip": a["ip"],
                    "invalid_user": False}

        return None  # ligne sans intérêt (sudo, cron, ...)
    except ValueError:
        logger.warning("Date invalide dans la ligne : %s", line[:100])
        return None
    except Exception:
        logger.exception("Erreur inattendue en parsant : %s", line[:100])
        return None