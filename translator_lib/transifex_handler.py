#!/usr/bin/env python3
"""
Transifex JSON Format Handler

Handles translation of Transifex JSON files with format:
{
  "key.name": "Value to translate",
  "another.key": "Another value"
}

Only the values are translated, keys remain unchanged.
"""

import json
import os
import sys
from typing import Dict, Optional, Tuple

from .core import translate_text, save_cache
from .format_handler import FormatHandler


class TransifexHandler(FormatHandler):
    """Handler for Transifex JSON translation files."""
    
    def __init__(self, *args, **kwargs):
        """Initialize Transifex JSON handler."""
        self.cache_file: Optional[str] = kwargs.pop('cache_file', None)
        super().__init__(*args, **kwargs)
        self.data_in: Optional[Dict[str, str]] = None
        self.data_out: Optional[Dict[str, str]] = None
        self.input_path: Optional[str] = None
    
    def load(self, input_path: str) -> None:
        """
        Load a Transifex JSON file.
        
        Args:
            input_path: Path to the input JSON file
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        self.input_path = input_path
        
        with open(input_path, 'r', encoding='utf-8') as f:
            self.data_in = json.load(f)
        
        if not isinstance(self.data_in, dict):
            raise ValueError(f"Expected JSON object at root level, got {type(self.data_in)}")
        
        if self.verbose:
            print(f"Loaded {len(self.data_in)} entries from {input_path}")
    
    def _load_existing_output(self, output_path: str) -> None:
        """
        Load existing output file for resume functionality.
        
        Args:
            output_path: Path to the existing output file
        """
        if os.path.exists(output_path):
            if self.verbose:
                print(f"Resuming from existing output: {output_path}")
            
            with open(output_path, 'r', encoding='utf-8') as f:
                self.data_out = json.load(f)
            
            if not isinstance(self.data_out, dict):
                self.data_out = {}
    
    def translate(self) -> Tuple[int, int]:
        """
        Translate all entries in the loaded JSON file.
        
        Returns:
            Tuple of (total_entries, translated_entries)
        """
        if self.data_in is None:
            raise RuntimeError("No input file loaded. Call load() first.")
        
        # Initialize output if not already loaded
        if self.data_out is None:
            self.data_out = {}
        
        total = 0
        translated = 0
        
        # Sort keys for consistent processing order
        keys = sorted(self.data_in.keys())
        
        for idx, key in enumerate(keys, start=1):
            total += 1
            value = self.data_in[key]
            
            # Skip if not a string (shouldn't happen in Transifex format, but be safe)
            if not isinstance(value, str):
                if self.verbose:
                    print(f"[SKIP] Entry {idx}: Key '{key}' has non-string value, skipping")
                self.data_out[key] = value
                continue
            
            # Skip if already translated and skip_translated is True
            if self.skip_translated and key in self.data_out and self.data_out[key].strip():
                if self.verbose:
                    print(f"[SKIP] Entry {idx}: Key '{key}' already translated")
                continue
            
            # Skip empty values
            if not value.strip():
                self.data_out[key] = value
                continue
            
            try:
                # Translate the value
                translated_value = translate_text(value, self.translator, cache=self.cache)
                
                # Check if actually changed
                if translated_value.strip() != value.strip():
                    translated += 1
                    if self.verbose:
                        snippet = value.replace("\n", " ")
                        if len(snippet) > 60:
                            snippet = snippet[:57] + "..."
                        trans_snippet = translated_value.replace("\n", " ")
                        if len(trans_snippet) > 60:
                            trans_snippet = trans_snippet[:57] + "..."
                        print(f"[OK] {idx}/{len(keys)} '{key}': '{snippet}' -> '{trans_snippet}'")
                
                self.data_out[key] = translated_value
                
            except Exception as e:
                print(f"[WARN] Entry {idx}: Key '{key}' translation error: {e}. Keeping original.", file=sys.stderr)
                self.data_out[key] = value
            
            # Checkpoint
            if self.verbose and idx % self.checkpoint_every == 0:
                print(f"[PROGRESS] {translated}/{total} translated so far...")
                if self.cache_file:
                    save_cache(self.cache, self.cache_file)
        
        return total, translated
    
    def save(self, output_path: str, dry_run: bool = False) -> None:
        """
        Save the translated JSON file.
        
        Args:
            output_path: Path to the output file
            dry_run: If True, don't actually write the file
        """
        if self.data_out is None:
            raise RuntimeError("No output to save. Call translate() first.")
        
        if dry_run:
            print(f"[DRY-RUN] Would write to {output_path}")
        else:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            
            # Write with pretty formatting (2-space indent to match common Transifex format)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.data_out, f, ensure_ascii=False, indent=2)
            
            print(f"Wrote translated file to {output_path}")
            
            # Persist cache
            if self.cache_file:
                save_cache(self.cache, self.cache_file)
