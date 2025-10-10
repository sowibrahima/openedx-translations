"""
Translator Library

A modular translation library supporting multiple file formats.
"""

from .core import (
    protect_placeholders,
    restore_placeholders,
    translate_text,
    cache_key,
    load_cache,
    save_cache,
)
from .format_handler import FormatHandler
from .po_handler import POHandler
from .transifex_handler import TransifexHandler

__all__ = [
    # Core utilities
    'protect_placeholders',
    'restore_placeholders',
    'translate_text',
    'cache_key',
    'load_cache',
    'save_cache',
    # Format handlers
    'FormatHandler',
    'POHandler',
    'TransifexHandler',
]
