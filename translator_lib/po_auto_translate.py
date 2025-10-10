#!/usr/bin/env python3
"""
PO Auto Translator

Reads an English .po file and writes a French .po file by translating only msgstr
fields using deep-translator (GoogleTranslator), while preserving:
- msgid/msgid_plural (unchanged)
- comments, flags, and reference locations (#:, #, etc.)
- placeholder tokens like %(name)s, %s, %d, {name}, {percent:.2%}
- HTML-like tags such as <strong>, <{strong}> blocks
- newlines and surrounding whitespace

Usage:
  python po_auto_translate.py -i /path/to/en.po -o /path/to/fr.po

Options:
  --skip-translated         Skip entries that already have a non-empty msgstr (default: True)
  --no-skip-translated      Do not skip (force re-translate)
  --dry-run                 Do everything except writing the output file

Notes:
- This script assumes source language is English and target language is French.
- It sets/updates French PO headers (Language, Plural-Forms) on output.
- For plural entries, it translates singular and plural separately into msgstr[0] and msgstr[1].
- Network access is required for GoogleTranslator.
"""

import argparse
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translator_lib import POHandler, load_cache


def main():
    parser = argparse.ArgumentParser(description="Translate PO file EN->FR into msgstr using GoogleTranslator.")
    parser.add_argument("-i", "--input", required=True, help="Path to English input .po file")
    parser.add_argument("-o", "--output", required=True, help="Path to French output .po file")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing output file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print progress and per-entry status")
    parser.add_argument("--checkpoint-every", type=int, default=50, help="Save partial output and cache every N entries (default: 50)")
    parser.add_argument("--resume", action="store_true", help="Resume from existing output file if present")
    parser.add_argument("--cache-file", default=None, help="Path to JSON cache file to store translations")
    skip_group = parser.add_mutually_exclusive_group()
    skip_group.add_argument("--skip-translated", dest="skip_translated", action="store_true", default=True,
                            help="Skip entries with existing msgstr (default)")
    skip_group.add_argument("--no-skip-translated", dest="skip_translated", action="store_false",
                            help="Do not skip already translated entries")

    args = parser.parse_args()

    try:
        # Load cache
        cache = load_cache(args.cache_file)
        
        # Create handler
        handler = POHandler(
            source_lang="en",
            target_lang="fr",
            skip_translated=args.skip_translated,
            verbose=args.verbose,
            checkpoint_every=args.checkpoint_every,
            cache=cache,
            cache_file=args.cache_file,
        )
        
        # Process file
        try:
            total, translated = handler.process_file(
                args.input,
                args.output,
                dry_run=args.dry_run,
                resume=args.resume,
            )
            print(f"Completed: {translated}/{total} entries translated")
        except KeyboardInterrupt:
            print("\n[INTERRUPTED] Attempting to save progress...", file=sys.stderr)
            print("Use --resume next run to continue from where you left off.", file=sys.stderr)
            raise
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
