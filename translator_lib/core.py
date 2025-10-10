#!/usr/bin/env python3
"""
Core Translation Utilities

Provides shared translation functionality that can be used across different file formats.
Includes placeholder protection, text translation, and caching mechanisms.
"""

import json
import os
import re
from typing import Dict, List, Tuple, Optional

from deep_translator import GoogleTranslator


# Pattern to match placeholders and HTML-like tags
PLACEHOLDER_PATTERN = re.compile(
    # Python old-style (printf), Python brace, and HTML-like tags
    r"(%\([^)]+\)[#0\- +]?[\d\.]*[sdif]|%[sdif]|\{[^}]+\}|<[^>]+>)"
)


def protect_placeholders(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Replace placeholders/tags in text with stable tokens and return mapping for restoration.
    
    Args:
        text: The text containing placeholders to protect
        
    Returns:
        Tuple of (protected_text, mapping_dict)
    """
    mapping: Dict[str, str] = {}

    def repl(match: re.Match) -> str:
        original = match.group(0)
        token = f"__PH_{len(mapping)}__"
        mapping[token] = original
        return token

    protected = PLACEHOLDER_PATTERN.sub(repl, text)
    return protected, mapping


def restore_placeholders(text: str, mapping: Dict[str, str]) -> str:
    """
    Restore original placeholders from tokens.
    
    Args:
        text: The text with placeholder tokens
        mapping: Dictionary mapping tokens to original placeholders
        
    Returns:
        Text with original placeholders restored
    """
    for token, original in mapping.items():
        text = text.replace(token, original)
    return text


def translate_text(
    text: str,
    translator: GoogleTranslator,
    cache: Optional[Dict[str, str]] = None
) -> str:
    """
    Translate text preserving newlines, surrounding whitespace, and placeholders.
    
    Args:
        text: The text to translate
        translator: GoogleTranslator instance configured with source and target languages
        cache: Optional cache dictionary for storing translations
        
    Returns:
        Translated text with preserved formatting and placeholders
    """
    if not text:
        return text

    # Preserve exact leading/trailing whitespace
    leading_ws = len(text) - len(text.lstrip(" \t"))
    trailing_ws = len(text) - len(text.rstrip(" \t"))
    prefix = text[:leading_ws]
    suffix = text[len(text) - trailing_ws:] if trailing_ws > 0 else ""

    core = text[leading_ws: len(text) - trailing_ws if trailing_ws > 0 else len(text)]

    # Split by explicit newlines to avoid Google collapsing layout
    parts = core.split("\n")
    translated_parts: List[str] = []

    for part in parts:
        # Protect placeholders and tags
        protected, mapping = protect_placeholders(part)
        if protected.strip():
            try:
                # Check translation cache by protected core
                translated = None
                if cache is not None:
                    ck = cache_key(protected)
                    translated = cache.get(ck)
                if translated is None:
                    translated = translator.translate(protected)
                    if cache is not None and translated is not None:
                        cache[ck] = translated
            except Exception:
                # Fallback to original on translation failure
                translated = protected
            # Some translator backends may return None without raising
            if translated is None:
                translated = protected
            translated = restore_placeholders(translated, mapping)
        else:
            translated = protected  # keep empty lines/whitespace-only
        translated_parts.append(translated)

    translated_core = "\n".join(translated_parts)
    return f"{prefix}{translated_core}{suffix}"


# -------------------------- Caching Utilities --------------------------

def cache_key(text: str) -> str:
    """
    Generate a cache key for the given text.
    
    Args:
        text: The text to generate a key for
        
    Returns:
        Cache key (currently just the text itself)
    """
    # Use the text itself as key; could switch to hash if file grows too large
    return text


def load_cache(cache_file: Optional[str]) -> Dict[str, str]:
    """
    Load translation cache from a JSON file.
    
    Args:
        cache_file: Path to the cache file
        
    Returns:
        Dictionary of cached translations, or empty dict if file doesn't exist
    """
    if not cache_file:
        return {}
    if not os.path.exists(cache_file):
        return {}
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def save_cache(cache: Dict[str, str], cache_file: Optional[str]) -> None:
    """
    Save translation cache to a JSON file.
    
    Args:
        cache: Dictionary of translations to save
        cache_file: Path to the cache file
    """
    if not cache_file:
        return
    tmp = cache_file + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=0)
    os.replace(tmp, cache_file)
