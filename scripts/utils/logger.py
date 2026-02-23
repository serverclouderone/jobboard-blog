"""
Logger coloré console + fichier. Utilisé par le pipeline et les scrapers.
"""
import os
import sys
from datetime import datetime

# Sera défini par main_pipeline ou rester None (console only)
LOG_FILE_PATH = None
ERRORS_LOG_PATH = None


def set_log_files(log_path=None, errors_path=None):
    global LOG_FILE_PATH, ERRORS_LOG_PATH
    LOG_FILE_PATH = log_path
    ERRORS_LOG_PATH = errors_path


def _write(path, line):
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def log(message, level="INFO"):
    """Affiche en console (couleurs si possible) et écrit dans le fichier log."""
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {message}"
    if level == "ERROR" and ERRORS_LOG_PATH:
        _write(ERRORS_LOG_PATH, line)
    if LOG_FILE_PATH:
        _write(LOG_FILE_PATH, line)
    if level == "ERROR":
        print(f"\033[91m{line}\033[0m", file=sys.stderr)
    elif level == "WARNING":
        print(f"\033[93m{line}\033[0m")
    else:
        print(line)
