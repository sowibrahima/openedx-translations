# Translator Library Architecture

## Overview

The translator library follows a **modular, extensible architecture** that separates core translation logic from format-specific implementations.

## Design Pattern: Strategy Pattern

The library uses the **Strategy Pattern** where:
- **Strategy Interface**: `FormatHandler` (abstract base class)
- **Concrete Strategies**: `POHandler`, `TransifexHandler`
- **Shared Context**: Core translation utilities

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Scripts Layer                        │
├─────────────────────────────────────────────────────────────┤
│  po_auto_translate.py    │  transifex_auto_translate.py     │
│  (CLI for PO files)      │  (CLI for JSON files)            │
└──────────────┬───────────┴──────────────┬───────────────────┘
               │                          │
               │  Uses                    │  Uses
               ▼                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Format Handlers Layer                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         FormatHandler (Abstract Base Class)          │  │
│  │  - load(input_path)                                  │  │
│  │  - translate() -> (total, translated)                │  │
│  │  - save(output_path, dry_run)                        │  │
│  │  - process_file(...)                                 │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│         ┌───────────┴───────────┐                           │
│         │                       │                           │
│         ▼                       ▼                           │
│  ┌─────────────┐         ┌──────────────────┐             │
│  │  POHandler  │         │ TransifexHandler │             │
│  │             │         │                  │             │
│  │ - Handles   │         │ - Handles JSON   │             │
│  │   .po files │         │   key-value      │             │
│  │ - Preserves │         │ - Simple format  │             │
│  │   metadata  │         │ - Fast parsing   │             │
│  │ - Plurals   │         │                  │             │
│  └─────────────┘         └──────────────────┘             │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            │  Uses
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Utilities Layer                    │
├─────────────────────────────────────────────────────────────┤
│  core.py                                                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │  • protect_placeholders(text)                      │    │
│  │    - Protects {var}, %(var)s, %s, <tags>           │    │
│  │                                                      │    │
│  │  • restore_placeholders(text, mapping)             │    │
│  │    - Restores original placeholders                │    │
│  │                                                      │    │
│  │  • translate_text(text, translator, cache)         │    │
│  │    - Preserves whitespace & newlines               │    │
│  │    - Uses cache to avoid redundant calls           │    │
│  │                                                      │    │
│  │  • load_cache(file) / save_cache(cache, file)      │    │
│  │    - Persistent translation cache                  │    │
│  └────────────────────────────────────────────────────┘    │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            │  Uses
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Dependencies                     │
├─────────────────────────────────────────────────────────────┤
│  • deep_translator.GoogleTranslator                          │
│  • polib (for PO files only)                                │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Translation Pipeline

```
Input File
    │
    ▼
┌─────────────────┐
│ Format Handler  │
│   .load()       │  ← Reads format-specific file
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Format Handler  │
│  .translate()   │  ← Iterates through entries
└────────┬────────┘
         │
         │  For each entry:
         ▼
┌─────────────────┐
│  Core Utils     │
│ translate_text()│  ← Protects placeholders
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Check Cache     │  ← Avoid redundant API calls
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GoogleTranslator│  ← Actual translation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Core Utils     │
│ restore_placeh..│  ← Restore placeholders
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Format Handler  │
│    .save()      │  ← Writes format-specific file
└────────┬────────┘
         │
         ▼
    Output File
```

## Key Design Decisions

### 1. Separation of Concerns

**Why**: Makes code maintainable and testable
- **Core utilities**: Format-agnostic translation logic
- **Format handlers**: Format-specific parsing/writing
- **CLI scripts**: User interface layer

### 2. Abstract Base Class (FormatHandler)

**Why**: Ensures consistent interface across formats
- All handlers implement the same methods
- Easy to add new formats
- Type safety and IDE support

### 3. Placeholder Protection Strategy

**Why**: Prevents translation of technical elements
- Regex-based detection
- Token replacement before translation
- Restoration after translation

### 4. Translation Caching

**Why**: Reduces API calls and improves performance
- JSON-based persistent cache
- Shared across runs
- Keyed by source text

### 5. Resume Capability

**Why**: Handle interruptions gracefully
- Load existing output
- Skip already translated entries
- Checkpoint saves during processing

## Extensibility

### Adding a New Format

To add support for a new format (e.g., XLIFF, Android XML):

1. **Create handler class**:
```python
class XLIFFHandler(FormatHandler):
    def load(self, input_path: str) -> None:
        # Parse XLIFF format
        pass
    
    def translate(self) -> Tuple[int, int]:
        # Use translate_text() from core
        pass
    
    def save(self, output_path: str, dry_run: bool = False) -> None:
        # Write XLIFF format
        pass
```

2. **Create CLI script**:
```python
from translator_lib import XLIFFHandler, load_cache

def main():
    # Standard CLI boilerplate
    pass
```

3. **Update exports**:
```python
# __init__.py
from .xliff_handler import XLIFFHandler
__all__ = [..., 'XLIFFHandler']
```

## Benefits of This Architecture

1. **DRY Principle**: Core logic written once, used everywhere
2. **Single Responsibility**: Each module has one clear purpose
3. **Open/Closed**: Open for extension, closed for modification
4. **Testability**: Each component can be tested independently
5. **Maintainability**: Changes isolated to specific modules
6. **Reusability**: Handlers can be used as library or CLI

## File Organization

```
translator_lib/
├── __init__.py              # Package exports
├── core.py                  # Shared utilities (format-agnostic)
├── format_handler.py        # Abstract base class
├── po_handler.py            # PO format implementation
├── transifex_handler.py     # JSON format implementation
├── po_auto_translate.py     # CLI for PO files
├── transifex_auto_translate.py  # CLI for JSON files
├── README.md                # User documentation
├── ARCHITECTURE.md          # This file
└── EXAMPLES.md              # Usage examples
```

## Testing Strategy

### Unit Tests
- Test core utilities independently
- Mock translator for deterministic tests
- Test placeholder protection/restoration

### Integration Tests
- Test complete translation pipeline
- Test with real file formats
- Test resume and caching

### Example Test Structure
```python
def test_placeholder_protection():
    text = "Hello {name}, you have %d messages"
    protected, mapping = protect_placeholders(text)
    assert "{name}" not in protected
    assert "%d" not in protected
    restored = restore_placeholders(protected, mapping)
    assert restored == text
```

## Future Enhancements

1. **Additional Formats**: XLIFF, Android XML, iOS Strings
2. **Multiple Translation Engines**: DeepL, Azure, AWS Translate
3. **Batch Processing**: Parallel translation of multiple files
4. **Quality Checks**: Validate placeholder consistency
5. **Progress Persistence**: SQLite for large-scale operations
6. **Language Detection**: Auto-detect source language
