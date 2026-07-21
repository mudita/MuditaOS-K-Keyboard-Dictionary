"""
Universal AOSP dictionary processing script.
Usage: python process_dict.py <file.combined>

Steps:
  1. Extracts the language code from the filename (main_XX.combined -> xx)
  2. Loads the profanity list and stop-words from profanity_data.py
  3. Creates a .bak backup of the input file
  4. Processes the file line by line (streaming):
     - adds ,possibly_offensive=true for words in the profanity set (minus stop-words)
     - removes ,possibly_offensive=true for words in the stop-words set (corrects false positives)
  5. Writes the result to Parsed/ and saves a list of found profanities
"""
import os
import re
import sys
import shutil

# profanity_data.py must be in the same directory as process_dict.py
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from profanity_data import PROFANITY_DB, STOP_WORDS_DB

WORD_RE = re.compile(r"^\s*(?:bigram|word)=([^,]+),")
OFFENSIVE_TAG = ",possibly_offensive=true"


def get_lang(filepath):
    """Extracts the lowercase language code from a filename like main_XX.combined."""
    basename = os.path.basename(filepath)
    m = re.match(r"main_(.+)\.combined$", basename, re.IGNORECASE)
    if m:
        return m.group(1).lower()
    return None


def main():
    if len(sys.argv) != 2:
        print("Usage: python process_dict.py <file.combined>")
        print("Example: python process_dict.py main_pl.combined")
        sys.exit(1)

    src_path = os.path.abspath(sys.argv[1])

    if not os.path.isfile(src_path):
        print(f"Error: file does not exist: {src_path}")
        sys.exit(1)

    lang = get_lang(src_path)
    if not lang:
        print(f"Error: cannot extract language code from: {os.path.basename(src_path)}")
        print("Expected filename format: main_XX.combined or main_XX_XX.combined")
        sys.exit(1)

    if lang not in PROFANITY_DB:
        print(f"Error: no data for language '{lang}' in profanity_data.py")
        print(f"Available languages: {', '.join(sorted(PROFANITY_DB.keys()))}")
        sys.exit(1)

    profanity = PROFANITY_DB[lang]
    stop_words = STOP_WORDS_DB.get(lang, set())
    effective = profanity - stop_words

    parsed_dir = os.path.join(_SCRIPT_DIR, "Parsed")
    os.makedirs(parsed_dir, exist_ok=True)

    src_basename = os.path.basename(src_path)
    bak_path = src_path + ".bak"
    dst_path = os.path.join(parsed_dir, src_basename)
    bak_dst = os.path.join(parsed_dir, src_basename + ".bak")
    vuln_list_path = os.path.join(parsed_dir, f"{lang}_lista_wulgaryzmow.txt")

    shutil.copy2(src_path, bak_path)

    print(f"Language:            {lang}")
    print(f"Words in database:   {len(profanity)}")
    print(f"Stop-words:          {len(stop_words)}")
    print(f"Effective:           {len(effective)}")
    print(f"Backup:              {bak_path}")
    print("Processing (streaming)...")

    found = set()
    total_words = 0
    newly_flagged = 0
    unflagged = 0

    with open(bak_path, "r", encoding="utf-8") as fin, \
         open(dst_path, "w", encoding="utf-8") as fout:
        for line in fin:
            s = line.rstrip("\n")
            m = WORD_RE.match(s)
            if m:
                total_words += 1
                word = m.group(1).lower()
                already_flagged = OFFENSIVE_TAG in s
                should_flag = word in effective

                if should_flag and not already_flagged:
                    s += OFFENSIVE_TAG
                    newly_flagged += 1
                    found.add(word)
                elif should_flag and already_flagged:
                    found.add(word)
                elif not should_flag and already_flagged:
                    s = s.replace(OFFENSIVE_TAG, "")
                    unflagged += 1
            fout.write(s + "\n")

    with open(vuln_list_path, "w", encoding="utf-8") as f:
        for w in sorted(found):
            f.write(w + "\n")

    shutil.move(bak_path, bak_dst)

    print(f"\n=== SUMMARY ===")
    print(f"Words checked:      {total_words}")
    print(f"Newly flagged:      {newly_flagged}")
    print(f"Unflagged:          {unflagged}")
    print(f"Unique profanities: {len(found)}")
    print(f"Result -> {dst_path}")
    print(f"Backup -> {bak_dst}")
    print(f"List   -> {vuln_list_path}")


if __name__ == "__main__":
    main()
