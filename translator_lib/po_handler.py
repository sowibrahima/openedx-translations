#!/usr/bin/env python3
"""
PO File Format Handler

Handles translation of .po (gettext) files while preserving:
- msgid/msgid_plural (unchanged)
- comments, flags, and reference locations
- placeholder tokens
- newlines and surrounding whitespace
"""

import os
import sys
from typing import Dict, Optional, Tuple

import polib

from .core import translate_text, save_cache
from .format_handler import FormatHandler


class POHandler(FormatHandler):
    """Handler for .po (gettext) translation files."""
    
    def __init__(self, *args, **kwargs):
        """Initialize PO handler."""
        self.cache_file: Optional[str] = kwargs.pop('cache_file', None)
        super().__init__(*args, **kwargs)
        self.po_in: Optional[polib.POFile] = None
        self.po_out: Optional[polib.POFile] = None
    
    def load(self, input_path: str) -> None:
        """
        Load a .po file.
        
        Args:
            input_path: Path to the input .po file
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        self.po_in = polib.pofile(input_path)
        
        if self.verbose:
            print(f"Loaded {len(self.po_in)} entries from {input_path}")
    
    def _load_existing_output(self, output_path: str) -> None:
        """
        Load existing output file for resume functionality.
        
        Args:
            output_path: Path to the existing output file
        """
        if os.path.exists(output_path):
            if self.verbose:
                print(f"Resuming from existing output: {output_path}")
            self.po_out = polib.pofile(output_path)
            self._update_headers()
    
    def _update_headers(self) -> None:
        """Ensure target language headers and plural forms are correct."""
        if self.po_out is None:
            return
        
        self.po_out.metadata["Language"] = self.target_lang
        
        # Set plural forms based on target language
        # French plural rule (can be extended for other languages)
        if self.target_lang == "fr":
            self.po_out.metadata["Plural-Forms"] = "nplurals=2; plural=(n > 1);"
        
        # Ensure encoding metadata
        self.po_out.metadata.setdefault("Content-Type", "text/plain; charset=utf-8")
        self.po_out.metadata.setdefault("Content-Transfer-Encoding", "8bit")
    
    def _translate_entry(self, entry: polib.POEntry) -> bool:
        """
        Translate a single PO entry.
        
        Args:
            entry: The PO entry to translate
            
        Returns:
            True if the entry was translated (changed), False otherwise
        """
        # Skip header/fuzzy empty msgid
        if entry.msgid == "":
            return False
        
        # Singular without plural
        if not entry.msgid_plural:
            if self.skip_translated and entry.msgstr.strip():
                return False
            
            before = entry.msgstr
            # Use msgid as source text
            source = entry.msgstr if entry.msgstr.strip() else entry.msgid
            entry.msgstr = translate_text(source, self.translator, cache=self.cache)
            return before.strip() != entry.msgstr.strip()
        
        # Plural forms
        if self.skip_translated and any(v.strip() for v in entry.msgstr_plural.values()):
            return False
        
        before = dict(entry.msgstr_plural)
        
        singular_src = entry.msgstr_plural.get(0, "").strip() or entry.msgid
        plural_src = entry.msgstr_plural.get(1, "").strip() or entry.msgid_plural
        
        entry.msgstr_plural[0] = translate_text(singular_src, self.translator, cache=self.cache)
        entry.msgstr_plural[1] = translate_text(plural_src, self.translator, cache=self.cache)
        
        # Check if changed
        return any(
            before.get(i, "").strip() != entry.msgstr_plural.get(i, "").strip()
            for i in [0, 1]
        )
    
    def translate(self) -> Tuple[int, int]:
        """
        Translate all entries in the loaded PO file.
        
        Returns:
            Tuple of (total_entries, translated_entries)
        """
        if self.po_in is None:
            raise RuntimeError("No input file loaded. Call load() first.")
        
        # Prepare output PO
        if self.po_out is None:
            self.po_out = polib.POFile()
            self.po_out.metadata = dict(self.po_in.metadata)
            if self.po_in.header:
                self.po_out.header = self.po_in.header
            self._update_headers()
        
        total = 0
        translated = 0
        
        # Build quick index of existing output entries to support resume
        def key_for(e: polib.POEntry) -> Tuple[Optional[str], str]:
            return (e.msgctxt, e.msgid)
        
        out_index: Dict[Tuple[Optional[str], str], polib.POEntry] = {
            key_for(e): e for e in self.po_out
        }
        
        for idx, entry in enumerate(self.po_in, start=1):
            total += 1
            
            # Find or create corresponding output entry
            k = key_for(entry)
            new_entry = out_index.get(k)
            
            if new_entry is None:
                new_entry = polib.POEntry(
                    msgid=entry.msgid,
                    msgid_plural=entry.msgid_plural,
                    msgstr=entry.msgstr,
                    msgstr_plural=dict(entry.msgstr_plural),
                    occurrences=list(entry.occurrences),
                    comment=entry.comment,
                    tcomment=entry.tcomment,
                    flags=list(entry.flags),
                    previous_msgctxt=entry.previous_msgctxt,
                    previous_msgid=entry.previous_msgid,
                    previous_msgid_plural=entry.previous_msgid_plural,
                    msgctxt=entry.msgctxt,
                    encoding=entry.encoding,
                )
                self.po_out.append(new_entry)
                out_index[k] = new_entry
            
            try:
                changed = self._translate_entry(new_entry)
                if changed:
                    translated += 1
                    if self.verbose:
                        occ = new_entry.occurrences[0] if new_entry.occurrences else ("", "")
                        loc = f"{occ[0]}:{occ[1]}" if occ and occ[0] else "<no-ref>"
                        snippet = (new_entry.msgid or "").replace("\n", " ")
                        if len(snippet) > 80:
                            snippet = snippet[:77] + "..."
                        print(f"[OK] {idx}/{len(self.po_in)} translated @ {loc}: {snippet}")
            except Exception as e:
                print(f"[WARN] Entry {idx}: translation error: {e}. Keeping original text.", file=sys.stderr)
            
            # Checkpoint
            if self.verbose and idx % self.checkpoint_every == 0:
                print(f"[PROGRESS] {translated}/{total} translated so far...")
                if self.cache_file:
                    save_cache(self.cache, self.cache_file)
        
        return total, translated
    
    def save(self, output_path: str, dry_run: bool = False) -> None:
        """
        Save the translated PO file.
        
        Args:
            output_path: Path to the output file
            dry_run: If True, don't actually write the file
        """
        if self.po_out is None:
            raise RuntimeError("No output to save. Call translate() first.")
        
        if dry_run:
            print(f"[DRY-RUN] Would write to {output_path}")
        else:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            self.po_out.save(output_path)
            print(f"Wrote translated file to {output_path}")
            
            # Persist cache
            if self.cache_file:
                save_cache(self.cache, self.cache_file)
