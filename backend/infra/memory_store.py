# infra/memory_store.py
"""
Memory Store Module
-------------------
Provides file-based persistence for agent artifacts.
Used for storing:
- Agent summaries
- Raw retrieved documents
- Strategy plans
- Final markdown reports

This is a simple filesystem-based store, separate from the database.
"""

import json
from pathlib import Path
from typing import Any, Optional, Union

from loguru import logger

# Constants
BASE_DIR = Path("data/memory_store")
BASE_DIR.mkdir(parents=True, exist_ok=True)


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "dict"):
            return obj.dict()
        if hasattr(obj, "to_json"):
            return obj.to_json()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)

def save_json(name: str, data: Any) -> bool:
    """
    Saves data as a JSON file.
    
    Args:
        name (str): Filename (without extension).
        data (Any): JSON-serializable data.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    path = BASE_DIR / f"{name}.json"
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, cls=CustomEncoder)
        return True
    except Exception as e:
        logger.error(f"❌ Error saving JSON {name}: {e}")
        return False


def load_json(name: str) -> Optional[Any]:
    """
    Loads data from a JSON file.
    
    Args:
        name (str): Filename (without extension).
        
    Returns:
        Optional[Any]: The loaded data, or None if file missing/error.
    """
    path = BASE_DIR / f"{name}.json"
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ Error loading JSON {name}: {e}")
        return None


def save_text(name: str, content: str) -> bool:
    """
    Saves content as a Markdown/Text file.
    
    Args:
        name (str): Filename (without extension).
        content (str): Text content.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    path = BASE_DIR / f"{name}.md"
    try:
        path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving text {name}: {e}")
        return False


def load_text(name: str) -> Optional[str]:
    """
    Loads content from a Markdown/Text file.
    
    Args:
        name (str): Filename (without extension).
        
    Returns:
        Optional[str]: The text content, or None if file missing/error.
    """
    path = BASE_DIR / f"{name}.md"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"❌ Error loading text {name}: {e}")
        return None
