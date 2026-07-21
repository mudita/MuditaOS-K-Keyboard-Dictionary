# AOSP Bigram Dictionary Moderation

Scripts for adding `possibly_offensive=true` flags to AOSP bigram dictionaries (`.combined` format).

---

## Overview

AOSP keyboard dictionaries use a plain-text format where each entry is a word or bigram with a frequency score. This toolset scans those entries against a curated profanity database and marks offensive words in-place:

```
 word=shit,f=45,possibly_offensive=true
 word=hello,f=980
  bigram=fuck,f=12,possibly_offensive=true
```

The database distinguishes between:
- **profanity** — words that should be flagged
- **stop-words** — words that appear on profanity lists but are false positives (e.g. common verbs, food, animals). These are used to *remove* incorrect flags if present.

---

## File Structure

```
├── process_dict.py          # Universal processing script (main tool)
├── profanity_data.py        # Profanity + stop-words database
└── Parsed/                  # Output directory
    ├── main_<lang>.combined      # Processed dictionary
    ├── main_<lang>.combined.bak  # Backup of the input before processing
    └── <lang>_lista_wulgaryzmow.txt  # Words actually found and flagged
```

---

## Quick Start

```bash
python process_dict.py main_de_CH.combined
python process_dict.py main_pt_BR.combined
python process_dict.py C:\path\to\main_sr.combined
```

The script accepts an absolute or relative path. The filename must follow the AOSP naming convention: `main_<LANG>.combined`.

---

## How `process_dict.py` Works

1. **Language detection** — extracts the language code from the filename (`main_de_CH.combined` → `de_ch`). The code is always normalised to lowercase for the database lookup.

2. **Database lookup** — loads the profanity set and stop-words for that language from `profanity_data.py`. If the language is not in the database, the script exits with an error listing all supported languages.

3. **Effective profanity set** — computed as `PROFANITY_DB[lang] - STOP_WORDS_DB[lang]`, so stop-words can never be flagged.

4. **Backup** — copies the input file to `<input>.bak` before any modifications.

5. **Streaming processing** — reads the file line by line (no full load into memory) and applies:
   - adds `,possibly_offensive=true` if the word is in the effective profanity set and not already flagged
   - removes `,possibly_offensive=true` if the word is in the stop-words set (corrects previous false positives)
   - leaves all other lines unchanged

6. **Output** — writes the processed file to `Parsed/` and moves the `.bak` there as well.

7. **Word list** — saves a sorted list of every profane word actually found in the dictionary to `Parsed/<lang>_lista_wulgaryzmow.txt`.

### Output summary

```
Language:            de_ch
Words in database:   243
Stop-words:          69
Effective:           174
Backup:              main_de_CH.combined.bak
Processing (streaming)...

=== SUMMARY ===
Words checked:      523418
Newly flagged:      891
Unflagged:          0
Unique profanities: 134
Result -> Parsed\main_de_CH.combined
Backup -> Parsed\main_de_CH.combined.bak
List   -> Parsed\de_ch_lista_wulgaryzmow.txt
```

---

## Supported Languages

| Code | Language |
|------|----------|
| `de_ch` | German (Switzerland) |
| `pt_br` | Portuguese (Brazil) |
| `sr` | Serbian (Cyrillic) |
| `sr_zz` | Serbian (Latin) |

---

## Error Cases

**Unknown language:**
```
Error: no data for language 'pl' in profanity_data.py
Available languages: de_ch, pt_br, sr, sr_zz
```

**File not found:**
```
Error: file does not exist: C:\path\to\main_xx.combined
```

**Wrong filename format:**
```
Error: cannot extract language code from: wordlist.combined
Expected format: main_XX.combined or main_XX_XX.combined
```

---

## Updating the Database

Edit `profanity_data.py` directly — it is a plain Python file with two dictionaries:

```python
PROFANITY_DB: dict[str, set[str]] = {
    "de_ch": {"arsch", "ficken", ...},
    "pt_br": {"boceta", "caralho", ...},
    # ...
}

STOP_WORDS_DB: dict[str, set[str]] = {
    "de_ch": {"brüste", "esel", ...},
    # ...
}
```

To add a new language, add an entry to both dictionaries (use an empty `set()` for stop-words if none are needed) and ensure the key matches the lowercase language code in the filename.

---

## `.combined` File Format

```
dictionary=main:de_ch,locale=de_CH,description=wordlist for de_CH,date=...,version=18
 word=hello,f=980
  bigram=good,f=45
 word=scheiße,f=45,possibly_offensive=true
  bigram=ficken,f=12,possibly_offensive=true
```

- Lines starting with ` word=` are unigrams; lines starting with `  bigram=` are bigrams.
- `f=` is the frequency/priority score used by the AOSP keyboard.
- `,possibly_offensive=true` is appended at the end of the line to flag a word.
- The script matches on the word value only (case-insensitive).
