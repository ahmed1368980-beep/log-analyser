import gzip
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def list_log_files(data_dir):
    """Retourne la liste triée des fichiers auth.log* du dossier Data."""
    data_dir = Path(data_dir)
    try:
        files = sorted(data_dir.glob("auth.log*"))
    except OSError:
        logger.exception("Impossible de lire le dossier %s", data_dir)
        return []
    if not files:
        logger.warning("Aucun fichier auth.log* trouvé dans %s", data_dir)
    else:
        logger.info("%d fichier(s) trouvé(s) dans %s", len(files), data_dir)
    return files


def read_log_file(path):
    """Lit un fichier .gz ou texte et renvoie ses lignes une par une."""
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    count = 0
    try:
        # "rt" = lecture en mode texte (même pour gzip)
        with opener(path, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                count += 1
                yield line.rstrip("\n")
        logger.info("%s lu : %d lignes", path.name, count)
    except FileNotFoundError:
        logger.error("Fichier introuvable : %s", path)
    except (gzip.BadGzipFile, EOFError):
        logger.error("Archive gzip corrompue : %s (%d lignes lues avant l'erreur)", path, count)
    except OSError:
        logger.exception("Erreur de lecture sur %s", path)