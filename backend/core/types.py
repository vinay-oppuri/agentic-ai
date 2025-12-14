# core/types.py
"""
Core Types Module
-----------------
Defines shared data structures used across the application.
Designed to be lightweight and avoid heavy dependencies like LangChain
where possible.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Document:
    """
    Represents a text document with associated metadata.
    Used for RAG (Retrieval Augmented Generation).
    """
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
