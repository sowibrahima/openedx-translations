# Usage Examples

## Example 1: Translate a Transifex JSON File

```bash
# Translate a Transifex JSON file from English to French
python translator_lib/transifex_auto_translate.py \
  -i translations/frontend-app-account/src/i18n/transifex_input.json \
  -o translations/frontend-app-account/src/i18n/fr.json \
  -v \
  --cache-file .transifex_cache.json
```

**Input** (`transifex_input.json`):
```json
{
  "account.settings.page.heading": "Account Settings",
  "account.settings.loading.message": "Loading...",
  "account.settings.loading.error": "Error: {error}"
}
```

**Output** (`fr.json`):
```json
{
  "account.settings.page.heading": "Paramètres du compte",
  "account.settings.loading.message": "Chargement...",
  "account.settings.loading.error": "Erreur: {error}"
}
```

Note: Placeholders like `{error}` are preserved!

## Example 2: Translate a PO File

```bash
# Translate a PO file from English to French
python translator_lib/po_auto_translate.py \
  -i translations/completion/completion/conf/locale/en/LC_MESSAGES/django.po \
  -o translations/completion/completion/conf/locale/fr/LC_MESSAGES/django.po \
  -v \
  --cache-file .po_cache.json
```

## Example 3: Resume Interrupted Translation

If a translation is interrupted (Ctrl+C), you can resume:

```bash
# Resume from where you left off
python translator_lib/transifex_auto_translate.py \
  -i input.json \
  -o output.json \
  --resume \
  --cache-file .cache.json
```

## Example 4: Using as a Library

You can also use the handlers programmatically in your own scripts:

```python
from translator_lib import TransifexHandler, load_cache

# Load cache
cache = load_cache('.cache.json')

# Create handler
handler = TransifexHandler(
    source_lang="en",
    target_lang="fr",
    skip_translated=True,
    verbose=True,
    cache=cache,
    cache_file='.cache.json'
)

# Process file
total, translated = handler.process_file(
    input_path='input.json',
    output_path='output.json',
    dry_run=False,
    resume=False
)

print(f"Translated {translated} out of {total} entries")
```

## Example 5: Batch Processing Multiple Files

```bash
#!/bin/bash
# Translate multiple Transifex JSON files

CACHE_FILE=".batch_cache.json"

for file in translations/*/src/i18n/transifex_input.json; do
    dir=$(dirname "$file")
    output="$dir/fr.json"
    
    echo "Processing: $file"
    python translator_lib/transifex_auto_translate.py \
        -i "$file" \
        -o "$output" \
        --cache-file "$CACHE_FILE" \
        -v
done

echo "Batch translation complete!"
```

## Example 6: Dry Run (Preview Without Saving)

```bash
# See what would be translated without actually writing files
python translator_lib/transifex_auto_translate.py \
  -i input.json \
  -o output.json \
  --dry-run \
  -v
```

## Example 7: Force Re-translate Everything

```bash
# Re-translate all entries, even if already translated
python translator_lib/transifex_auto_translate.py \
  -i input.json \
  -o output.json \
  --no-skip-translated \
  --cache-file .cache.json
```

## Tips

1. **Always use `--cache-file`** to avoid redundant API calls and speed up translations
2. **Use `-v` (verbose)** to see progress for large files
3. **Use `--resume`** if you need to interrupt and continue later
4. **Use `--dry-run`** first to preview what will be translated
5. **Share cache files** across multiple translation runs to maximize efficiency
