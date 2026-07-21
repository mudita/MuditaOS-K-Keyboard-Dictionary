# Dictionary Processing Tools

This directory contains a set of Python scripts used to process, convert, and extend dictionaries for the KompaktOS keyboard. Each script has a specific task related to preparing dictionary data for different languages.

---

## 📋 Table of Contents

1. [dictionary_filter.py](#1-dictionary_filterpy) - Dictionary size optimizer
2. [converter_to_pt_br.py](#2-converter_to_pt_brpy) - Portuguese converter (PT-PT → PT-BR)
3. [cyrlica_to_latin.py](#3-cyrlica_to_latinpy) - Alphabet converter (Cyrillic → Latin)
4. [de_ch_wiki_parser.py](#4-de_ch_wiki_parserpy) - Wikipedia parser for Swiss German
5. [leipzig_words_parser.py](#5-leipzig_words_parserpy) - Leipzig corpus integration with AOSP

---

## 1. dictionary_filter.py

### Description
A tool for optimizing and reducing dictionary size by removing low-frequency words. It analyzes `.combined` files and intelligently reduces the word count when it exceeds a configurable threshold. The tool supports two reduction methods: frequency-based filtering and physical cutoff with a safety limit.

### Features
- **Automatic detection**: Scans all `.combined` files in the current directory
- **Smart filtering**: Removes words based on frequency (`f=` parameter)
- **Safety limit**: Prevents excessive reduction (default max 20%)
- **Physical cutoff**: Alternative method when frequency filtering would be too aggressive
- **Bigram preservation**: Keeps bigrams for retained words, removes them for deleted words
- **Preview mode**: Shows what would be changed without writing files
- **Verification**: Reports actual word count after file is written

### Usage

```bash
# Preview mode - analyze without writing changes
python dictionary_filter.py

# Apply changes and save to 'fixed' folder
python dictionary_filter.py --fix

# Custom word limit threshold (trigger optimization at 2M words)
python dictionary_filter.py --fix --word-size 2000000

# Custom reduction ratio (remove 35% of lowest-frequency words)
python dictionary_filter.py --fix --reduce-size 0.35

# Custom output directory
python dictionary_filter.py --fix --output-dir "optimized"

# Combine all options
python dictionary_filter.py --fix --word-size 2000000 --reduce-size 0.30 --output-dir "reduced"
```

### Parameters
- `--fix` - Enables write mode (saves modified files to disk)
- `--word-size X` - Word limit that triggers optimization (default: 3,000,000)
- `--reduce-size X` - Reduction ratio, e.g., 0.20 = 20% (default: 0.20)
- `--output-dir DIRNAME` - Output folder name (default: 'fixed')

### How it works
1. **Analysis**: Counts total words and their frequencies in each `.combined` file
2. **Threshold check**: If word count > `MAX_WORDS_LIMIT`, optimization is triggered
3. **Frequency sorting**: Calculates frequency threshold based on reduction ratio
4. **Safety check**: Ensures removal doesn't exceed the safety limit
5. **Removal method**:
   - **Frequency filtering**: Removes words with `f <= threshold`
   - **Physical cutoff**: When threshold is too aggressive, removes from the end
6. **Bigram handling**: Automatically removes bigrams for deleted words
7. **Output**: Saves optimized file to output directory with verification

### Example output
```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
 OPTIMIZATION: en_wordlist.combined
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
 -> Method:        Frequency filtering (f <= 45)
 -> Input words:   3,250,000
 -> Removed:       650,000 words
 -> Remaining:     2,600,000 words
 [VERIFICATION] File on disk contains: 2,600,000 words.
============================================================
```

### Requirements
- Python 3.x
- Input files in AOSP `.combined` format

### Notes
- The script processes all `.combined` files in the current directory
- Both `TARGET_REDUCTION_RATIO` and `SAFETY_MAX_REDUCTION` are set by `--reduce-size`
- Bigrams are automatically preserved for remaining words
- Output files maintain proper AOSP dictionary format

---

## 2. converter_to_pt_br.py

### Description
A script that converts a Portuguese dictionary from the European variant (PT-PT) to the Brazilian variant (PT-BR). It performs both orthographic transformations (e.g. *"facto"* → *"fato"*) and optional lexical replacements (e.g. *"autocarro"* → *"ônibus"*).

### Features
- **Orthographic conversions**: Automatic word replacements according to Brazilian orthographic reforms (e.g. removing silent consonants)
- **Lexical conversions (safe)**: Replaces basic vocabulary differences (e.g. *"telemóvel"* → *"celular"*)
- **Lexical conversions (aggressive)**: Additional colloquial replacements (optional)
- **Root protection**: A list of protected word roots that must not be converted
- **Blacklist**: Words blocked from being converted
- **Change preview**: Option to show changes without writing output

### Usage

```bash
# Preview changes (no writing)
python converter_to_pt_br.py path/to/pt_PT_wordlist.combined

# Convert and write
python converter_to_pt_br.py path/to/pt_PT_wordlist.combined --fix

# Convert with aggressive lexical changes
python converter_to_pt_br.py path/to/pt_PT_wordlist.combined --fix --aggressive
```

### Parameters
- `file` - Path to the PT-PT dictionary file (`.combined` format)
- `--fix` - Writes changes to a new file (`.fixed`)
- `--aggressive` - Enables aggressive lexical conversions

### Example conversions
| PT-PT | PT-BR | Type |
|-------|-------|------|
| autocarro | ônibus | Lexical |
| telemóvel | celular | Lexical |
| projecto | projeto | Orthographic |
| facto | fato | Orthographic |
| óptimo | ótimo | Orthographic |

### Requirements
- Python 3.x
- Input file in AOSP `.combined` format

---

## 2. cyrlica_to_latin.py

### Description
A simple text converter from the Cyrillic alphabet to the Latin alphabet, specifically tailored for Serbian. It preserves correct transliterations for Serbian-specific characters.

### Features
- Full transliteration of the Serbian Cyrillic alphabet
- Support for special characters (Ђ → Đ, Ћ → Ć, Љ → Lj, Њ → Nj, Џ → Dž, etc.)
- Preserves letter case
- UTF-8 encoding

### Usage

```bash
python cyrlica_to_latin.py input_file.combined output_file.combined
```

### Parameters
- `input_file` - Input file with Cyrillic text
- `output_file` - Output file with Latin text

### Example conversions
| Cyrillic | Latin |
|----------|-------|
| Београд | Beograd |
| Србија | Srbija |
| ђак | đak |
| љубав | ljubav |
| њива | njiva |

### Requirements
- Python 3.x
- Files encoded in UTF-8

---

## 3. de_ch_wiki_parser.py

### Description
An advanced Wikipedia parser for Alemannic (Swiss German - Alemannisch) that extracts vocabulary and bigrams for the keyboard dictionary. The script analyzes a Wikipedia XML dump, filters technical artifacts, and grows an existing dictionary with new words.
https://dumps.wikimedia.org/alswiki/20260401/alswiki-20260401-pages-articles.xml.bz2
After adaptation, it can be used for other languages by modifying the filtering and text-cleaning rules.

### Features
- **Wikipedia XML parsing**: Processing large Wikipedia dump files
- **Wiki text cleaning**: Removing MediaWiki tags, templates, and code
- **Smart filtering**:
  - Whitelist for short Alemannic words
  - Blacklist for technical words (Lua, MediaWiki, UI)
  - Filtering foreign-language words (French, English)
  - Removing Roman numerals and codes
- **Bigram extraction**: Analyzing word sequences for text prediction
- **Character normalization**: Handling ß/ss and diacritics
- **Frequency scaling**: Logarithmic rescaling to 0-255

### Usage

```bash
# Make sure the directory contains:
# - a *.combined file (base dictionary)
# - alswiki-20260401-pages-articles.xml (Wikipedia dump)

python de_ch_wiki_parser.py
```

### Configuration (in the file)
```python
MIN_WORD_COUNT = 500         # Min. occurrences of a word in Wikipedia
MIN_BIGRAM_COUNT = 10        # Min. occurrences of a bigram
MAX_WORD_LEN = 48           # Maximum word length
WIKI_FILE = "alswiki-20260401-pages-articles.xml"
REPORT_FILE = "added_words.txt"  # Report of added words
```

### Output
- `<name>.combined.grown` - Extended dictionary
- `added_words.txt` - List of added words

### Requirements
```bash
pip install lxml mwparserfromhell
```

### Notes
- The Wikipedia dump can be downloaded from https://dumps.wikimedia.org/alswiki/
- Processing may take a few minutes depending on the dump size
- The script requires at least ~2GB RAM for the full dump

---

## 4. leipzig_words_parser.py

### Description
A professional tool for integrating Leipzig language corpora with an existing AOSP dictionary. The script enriches the dictionary with bigrams from real-world text and optionally updates word frequency weights based on the corpus.

### Features
- **Bigram integration**: Adds up to 3 best bigrams per word
- **Frequency update**: Optional recalculation of `f` weights based on the Leipzig corpus
- **Unicode normalization**: Correct handling of diacritics (NFC)
- **Validation**: Filters invalid words and characters
- **Logarithmic scaling**: Weights 0-255 for optimal prediction
- **Preserves formatting**: Compatible with the AOSP `.combined` format

### Usage

```bash
# Basic usage (only adds bigrams)
python leipzig_words_parser.py path/to/dictionary.combined (without bigrams)

# With frequency weight update
python leipzig_words_parser.py path/to/dictionaries --update-freq

# In the current directory
python leipzig_words_parser.py (auto-detects combined and Leipzig word/bigram pairs)
```

### Parameters
- `path` - Path to the dictionary directory (default: current directory)
- `-u, --update-freq` - Updates `f` frequency weights based on the Leipzig corpus

### Required files
The working directory must contain:
- `*.combined` - Base AOSP dictionary
- `<language>-words.txt` - Leipzig word list with frequencies
- `<language>-co_n.txt` - Leipzig bigram data

### Example directory structure
```
dictionaries/
├── pl_wordlist.combined
├── pol_wikipedia_2021-words.txt
└── pol_wikipedia_2021-co_n.txt
```

### Leipzig data format
Files can be downloaded from: https://wortschatz.uni-leipzig.de/en/download
Example for en: https://wortschatz.uni-leipzig.de/en/download/eng

You can download multiple .gz files and extract them into one location. The script will automatically find all word/bigram pairs.

**`-words.txt` format:**
```
1    word    1234
2    text    987
```

**`-co_n.txt` format:**
```
1    2    15.5
```

### Output
- `<name>.bigram` - Enriched dictionary with bigrams
- Console report with statistics

### Requirements
- Python 3.x
- `unicodedata` module (standard library)

### Notes
- The script processes multiple Leipzig file pairs at once
- Bigram weights are computed as `word_f - 10` (max 120)
- Preserves the original header and formatting

---

## 📦 `.combined` file format

All scripts work with the AOSP dictionary format:

```
dictionary=main:pl,locale=pl,description=Polish,date=1712345678,version=1
 word=przykład,f=200,flags=,originalFreq=200
  bigram=tekstu,f=150
  bigram=użycia,f=120
 word=słowo,f=180,flags=,originalFreq=180
  bigram=kluczowe,f=140
```

### Structure
- **Header**: Dictionary metadata
- **Words**: A line starting with `word=`, with frequency weight `f=` (0-255)
- **Bigrams**: Indented by 2 spaces, up to 3 per word

---

