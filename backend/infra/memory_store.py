"""
infra/memory_store.py
---------------------
Handles file-based memory (agent summaries, raw docs, strategy, reports).
Central place for reading/writing persisted data.
"""

import json
from pathlib import Path
from loguru import logger


BASE_DIR = Path("data/memory_store")
BASE_DIR.mkdir(parents=True, exist_ok=True)


def save_json(name: str, data):
    path = BASE_DIR / f"{name}.json"
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"❌ Error saving {name}: {e}")
        return False


def load_json(name: str):
    path = BASE_DIR / f"{name}.json"
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ Error loading {name}: {e}")
        return None


def save_text(name: str, content: str):
    path = BASE_DIR / f"{name}.md"
    try:
        path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving markdown: {e}")
        return False


def load_text(name: str):
    path = BASE_DIR / f"{name}.md"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"❌ Error loading markdown: {e}")
        return None
