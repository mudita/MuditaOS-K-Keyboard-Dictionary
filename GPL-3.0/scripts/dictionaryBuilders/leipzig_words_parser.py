import math
import os
import re
import sys
import argparse
import unicodedata

def is_clean_word(word):
    """Checks whether the word consists of letters or allowed hyphens (e.g., Portuguese)."""
    if not word: return False
    # Allow letters and an internal hyphen (e.g., dar-se)
    clean = word.replace('-', '')
    return bool(clean.isalpha())

def normalize_text(text):
    """Unicode NFC normalization (critical for correct matching of diacritics)."""
    return unicodedata.normalize('NFC', text.strip().lower())

def parse_combined_line(line):
    """Extracts the word and the f weight from a line like 'word=...', ignoring indentation."""
    clean_line = line.strip()
    w_match = re.search(r'word=([^,]+)', clean_line)
    f_match = re.search(r'f=(\d+)', clean_line)
    if w_match and f_match:
        raw_word = w_match.group(1).strip()
        return normalize_text(raw_word), int(f_match.group(1)), raw_word
    return None, None, None

def calculate_f_score(count, max_count):
    """Compute the f weight on a 0-255 scale using a logarithmic scale."""
    if count <= 0 or max_count <= 1: return 1
    score = int(255 * (math.log(count) / math.log(max_count)))
    return max(1, min(255, score))

def main():
    parser = argparse.ArgumentParser(description="AOSP Keyboard Dictionary Tool - Professional Version")
    parser.add_argument("path", nargs="?", default=os.getcwd(), help="Path to the folder with files (defaults to current)")
    parser.add_argument("-u", "--update-freq", action="store_true", help="Update the f frequency based on Leipzig data")
    args = parser.parse_args()

    work_dir = args.path
    print("-" * 70)
    print(f"[START] Location: {work_dir}")
    print(f"[MODE] Update f: {'ENABLED' if args.update_freq else 'DISABLED'}")
    print("-" * 70)

    # 1. Find .combined files
    combined_files = [f for f in os.listdir(work_dir) if f.endswith('.combined')]
    if not combined_files:
        print("[ERROR] No .combined file found in the specified location.")
        return
    
    file_in = os.path.join(work_dir, combined_files[0])
    file_out = os.path.join(work_dir, combined_files[0].replace('.combined', '.bigram'))
    print(f"[INFO] Found source file: {combined_files[0]}")

    # 2. Find Leipzig file pairs (-words.txt and -co_n.txt)
    all_files = os.listdir(work_dir)
    word_files = [f for f in all_files if f.endswith('-words.txt')]
    pairs = []
    for wf in word_files:
        prefix = wf.replace('-words.txt', '')
        cf = f"{prefix}-co_n.txt"
        if cf in all_files:
            pairs.append((wf, cf))
    
    if not pairs:
        print("[ERROR] No -words.txt / -co_n.txt pairs found.")
        return
    print(f"[INFO] Found Leipzig data pairs: {len(pairs)}")

    # 3. Load .combined file
    header_lines = []
    words_data = [] 
    
    print(f"[INFO] Loading dictionary structure...")
    with open(file_in, 'r', encoding='utf-8-sig') as f:
        for line in f:
            clean_line = line.strip()
            if clean_line.startswith('word='):
                w_norm, f_val, w_orig = parse_combined_line(line)
                if w_norm:
                    flags_match = re.search(r'flags=([^,]*)', clean_line)
                    flags = flags_match.group(1) if flags_match else ""
                    
                    words_data.append({
                        'word_norm': w_norm,
                        'word_orig': w_orig,
                        'f': f_val,
                        'flags': flags,
                        'bigrams': []
                    })
            elif clean_line.startswith('bigram='):
                b_match = re.search(r'bigram=([^,]+)', clean_line)
                bf_match = re.search(r'f=(\d+)', clean_line)
                if b_match and bf_match and words_data:
                    words_data[-1]['bigrams'].append((b_match.group(1).strip(), int(bf_match.group(1))))
            elif not words_data:
                # Preserve header and blank lines before the word entries
                header_lines.append(line)

    source_words_count = len(words_data)
    print(f"[STAT] Number of source words: {source_words_count}")
    print("-" * 70)

    # Index for quick access (map by normalized word)
    word_map = {entry['word_norm']: entry for entry in words_data}

    # 4. Process Leipzig sources
    for w_file, c_file in pairs:
        print(f"\n>>> PROCESSING: {w_file}")
        l_id_to_word, l_word_to_id, l_counts, l_max_count = {}, {}, {}, 0
        
        with open(os.path.join(work_dir, w_file), 'r', encoding='utf-8-sig') as f:
            for line in f:
                p = line.split('\t')
                if len(p) >= 3:
                    wid, txt, count = p[0].strip(), p[1].strip(), int(p[2])
                    if is_clean_word(txt):
                        norm_txt = normalize_text(txt)
                        if norm_txt not in l_counts or count > l_counts[norm_txt]:
                            l_id_to_word[wid] = txt
                            l_word_to_id[norm_txt] = wid
                            l_counts[norm_txt] = count
                        if count > l_max_count: l_max_count = count
        
        l_bigrams = {}
        with open(os.path.join(work_dir, c_file), 'r', encoding='utf-8-sig') as f:
            for line in f:
                p = line.split('\t')
                if len(p) >= 3:
                    id1, id2, strength = p[0].strip(), p[1].strip(), p[2].strip()
                    if id1 in l_id_to_word and id2 in l_id_to_word:
                        if id1 not in l_bigrams: l_bigrams[id1] = []
                        try:
                            l_bigrams[id1].append((l_id_to_word[id2], float(strength.replace(',', '.'))))
                        except: continue

        # Update AOSP base dictionary
        added_bi = 0
        updated_f = 0
        for w_norm, entry in word_map.items():
            # Optional update of the f weight
            if args.update_freq and w_norm in l_counts:
                new_f = calculate_f_score(l_counts[w_norm], l_max_count)
                if new_f != entry['f']:
                    entry['f'] = new_f
                    updated_f += 1
            
            if len(entry['bigrams']) < 3 and w_norm in l_word_to_id:
                wid = l_word_to_id[w_norm]
                if wid in l_bigrams:
                    sorted_bi = sorted(l_bigrams[wid], key=lambda x: x[1], reverse=True)
                    existing_bi_norms = {normalize_text(b[0]) for b in entry['bigrams']}
                    
                    for b_word, b_strength in sorted_bi:
                        if len(entry['bigrams']) >= 3: break
                        b_norm = normalize_text(b_word)
                        if b_norm not in existing_bi_norms and is_clean_word(b_word):
                            # Bigram weight: word's f - 10 (max 120)
                            b_f = max(1, min(entry['f'] - 10, 120))
                            entry['bigrams'].append((b_word, b_f))
                            existing_bi_norms.add(b_norm)
                            added_bi += 1
        
        print(f"    [LOG] New bigrams: {added_bi}")
        if args.update_freq: print(f"    [LOG] Updated f weights: {updated_f}")

    # 5. Final sorting and saving
    print("\n" + "-" * 70)
    print(f"[INFO] Sorting dictionary (f-descending) and saving to {file_out}...")
    words_data.sort(key=lambda x: x['f'], reverse=True)

    with open(file_out, 'w', encoding='utf-8') as f:
        for h_line in header_lines:
            f.write(h_line)

        for entry in words_data:
            # One space before word=
            f.write(f" word={entry['word_orig']},f={entry['f']},flags={entry['flags']},originalFreq={entry['f']}\n")
            
            # Sort bigrams of given word and save (two spaces before bigram=)
            final_bi = sorted(entry['bigrams'], key=lambda x: x[1], reverse=True)[:3]
            for b_word, b_f in final_bi:
                f.write(f"  bigram={b_word},f={b_f}\n")

    print(f"[SUCCESS] Done! Processed {source_words_count} words.")
    print("-" * 70)

if __name__ == "__main__":
    main()