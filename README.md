# MuditaOS K Keyboard Dictionary

Keyboard prediction dictionaries for MuditaOS, in the AOSP keyboard dictionary format. Dictionaries are grouped by the license that applies to their source data.

## Repository Structure

```
├── CC-BY-SA-4.0/          # Dictionaries sourced under CC-BY-SA 4.0
│   ├── LICENSE            # Full CC-BY-SA 4.0 license text
│   └── dicts/             # Compiled binary dictionaries (.dict)
│
└── GPL-3.0/               # Dictionaries sourced under GPL-3.0
    ├── LICENSE            # Full GPL-3.0 license text
    ├── dicts/             # Compiled binary dictionaries (.dict)
    ├── wordslist/         # Source wordlists (.combined, plain text) used to build the .dict files
    └── scripts/           # Tools used to build and process the wordlists/dictionaries
        ├── dictionaryBuilders/    # See dictionaryBuilders/README.md
        └── cursedWordsCleaner/    # See cursedWordsCleaner/README.md
```

### `CC-BY-SA-4.0/`

Contains only compiled `.dict` binaries (`main_be.dict` — Belarusian, `main_sk.dict` — Slovak) plus the [LICENSE](CC-BY-SA-4.0/LICENSE) that applies to them. CC-BY-SA 4.0 does not require publishing build scripts or source wordlists, so no `wordslist/` or `scripts/` directory is present here.

### `GPL-3.0/`

Contains the full pipeline for its dictionaries (`de_ch`, `pt_br`, `sr`, `sr_zz`), plus the [LICENSE](GPL-3.0/LICENSE) that applies to them:
- `wordslist/` — the `.combined` text wordlists (word/bigram entries with frequency scores) that the `.dict` binaries are built from.
- `dicts/` — the compiled binary dictionaries used by the keyboard.
- `scripts/` — the Python tools used to build and clean the wordlists (see below).

## Scripts

| Script directory | Purpose | Docs |
|---|---|---|
| [dictionaryBuilders](GPL-3.0/scripts/dictionaryBuilders/README.md) | Build, convert, and extend `.combined` wordlists (size optimization, PT-PT → PT-BR conversion, Cyrillic → Latin transliteration, Wikipedia/Leipzig corpus integration) | [README](GPL-3.0/scripts/dictionaryBuilders/README.md) |
| [cursedWordsCleaner](GPL-3.0/scripts/cursedWordsCleaner/README.md) | Flag offensive words/bigrams in `.combined` dictionaries with `possibly_offensive=true` | [README](GPL-3.0/scripts/cursedWordsCleaner/README.md) |

Each script directory has its own README with detailed usage instructions, parameters, and examples — follow the links above for details.

## File Formats

- **`.combined`** — plain-text AOSP dictionary source format: one `word=` line per entry (with a frequency score `f=`), followed by up to a few indented `bigram=` lines.
- **`.dict`** — compiled binary AOSP dictionary format, consumed directly by the keyboard. Compiling `.combined` files into `.dict` binaries requires an external AOSP tool that is not part of this repository. This external tool is available here: https://android.googlesource.com/platform/packages/inputmethods/LatinIME/+/refs/heads/main/tools/dicttool/

## Notes

- Not all languages have build scripts/wordlists in this repo — see the [`CC-BY-SA-4.0/`](#cc-by-sa-40) section above.
