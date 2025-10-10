# Translator Library

A modular translation library supporting multiple file formats with shared core translation logic.

## Architecture

The library is designed with modularity in mind:

```
translator_lib/
├── core.py                      # Shared translation utilities
├── format_handler.py            # Base interface for format handlers
├── po_handler.py                # PO file format handler
├── transifex_handler.py         # Transifex JSON format handler
├── po_auto_translate.py         # CLI script for PO files
└── transifex_auto_translate.py  # CLI script for Transifex JSON
```

### Core Components

#### 1. **core.py** - Shared Translation Logic
Contains format-agnostic utilities:
- **Placeholder Protection**: Protects placeholders like `{name}`, `%(var)s`, `%s`, HTML tags during translation
- **Text Translation**: Preserves whitespace, newlines, and formatting while translating
- **Caching**: Stores translations to avoid redundant API calls

#### 2. **format_handler.py** - Base Interface
Abstract base class defining the interface all format handlers must implement:
- `load(input_path)`: Load input file
- `translate()`: Translate content
- `save(output_path)`: Save translated content
- `process_file()`: Complete workflow

#### 3. **Format Handlers**
Implement format-specific logic:

**POHandler** (`po_handler.py`):
- Handles gettext `.po` files
- Preserves msgid, comments, flags, occurrences
- Handles plural forms
- Updates language-specific headers

**TransifexHandler** (`transifex_handler.py`):
- Handles Transifex JSON files
- Simple key-value format
- Only translates values, preserves keys

## Usage

### PO Files

```bash
# Basic usage
python translator_lib/po_auto_translate.py -i input.po -o output.po

# With verbose output and caching
python translator_lib/po_auto_translate.py \
  -i input.po \
  -o output.po \
  -v \
  --cache-file .cache.json

# Resume interrupted translation
python translator_lib/po_auto_translate.py \
  -i input.po \
  -o output.po \
  --resume \
  --cache-file .cache.json
```

### Transifex JSON Files

```bash
# Basic usage
python translator_lib/transifex_auto_translate.py -i input.json -o output.json

# With verbose output and caching
python translator_lib/transifex_auto_translate.py \
  -i input.json \
  -o output.json \
  -v \
  --cache-file .cache.json

# Force re-translate all entries
python translator_lib/transifex_auto_translate.py \
  -i input.json \
  -o output.json \
  --no-skip-translated
```

## Command-Line Options

Both scripts support the same options:

| Option | Description |
|--------|-------------|
| `-i, --input` | Path to input file (required) |
| `-o, --output` | Path to output file (required) |
| `-v, --verbose` | Print progress and per-entry status |
| `--dry-run` | Run without writing output file |
| `--skip-translated` | Skip already translated entries (default) |
| `--no-skip-translated` | Force re-translate all entries |
| `--resume` | Resume from existing output file |
| `--cache-file` | Path to JSON cache file |
| `--checkpoint-every` | Save progress every N entries (default: 50) |

## Adding New Formats

To add support for a new format:

1. **Create a new handler** in `translator_lib/new_format_handler.py`:

```python
from translator_lib.format_handler import FormatHandler
from translator_lib.core import translate_text

class NewFormatHandler(FormatHandler):
    def load(self, input_path: str) -> None:
        # Load your format
        pass
    
    def translate(self) -> Tuple[int, int]:
        # Translate using translate_text() from core
        pass
    
    def save(self, output_path: str, dry_run: bool = False) -> None:
        # Save your format
        pass
```

2. **Create a CLI script** in `translator_lib/new_format_auto_translate.py`:

```python
from translator_lib import NewFormatHandler, load_cache

def main():
    # Parse arguments
    # Create handler
    # Process file
    pass
```

3. **Update `__init__.py`** to export your handler

## Features

### Placeholder Protection
Automatically protects and restores:
- Python format strings: `%(name)s`, `%s`, `%d`
- Brace placeholders: `{name}`, `{error}`
- HTML tags: `<strong>`, `<a href="...">`

### Whitespace Preservation
- Leading/trailing whitespace preserved
- Newlines maintained
- Formatting intact

### Translation Caching
- Avoid redundant API calls
- Resume interrupted translations
- Persistent across runs

### Progress Tracking
- Verbose mode shows per-entry progress
- Checkpoint saves every N entries
- Resume support for long translations

## Dependencies

- `deep-translator`: Translation API wrapper
- `polib`: PO file parsing (for PO format only)

Install with:
```bash
pip install deep-translator polib
```

## Design Principles

1. **Separation of Concerns**: Core logic separated from format-specific code
2. **Extensibility**: Easy to add new formats
3. **Reusability**: Shared utilities used across all formats
4. **Robustness**: Error handling, caching, resume support
5. **User-Friendly**: Clear CLI, progress tracking, helpful messages
