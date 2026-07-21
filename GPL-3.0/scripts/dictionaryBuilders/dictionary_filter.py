import os
import re
import argparse

# --- DEFAULT PARAMETERS ---
MAX_WORDS_LIMIT = 3000000
TARGET_REDUCTION_RATIO = 0.20
SAFETY_MAX_REDUCTION = 0.20
OUTPUT_FOLDER = 'fixed'

def verify_fixed_file(file_path, expected_count):
    word_pattern = re.compile(r"^\s*word=")
    actual_count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if word_pattern.match(line):
                    actual_count += 1
        print(f" [VERIFICATION] File on disk contains: {actual_count:,} words.")
    except Exception as e:
        print(f" [VERIFICATION] Error while checking file: {e}")

def process_combined_file(file_path, fix_mode):
    word_pattern = re.compile(r"^\s*word=([^,]+),f=(\d+)")
    bigram_pattern = re.compile(r"^\s*bigram=([^,]+),f=(\d+)")

    all_lines = []
    word_indices = [] 
    frequencies = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                all_lines.append(line)
                match = word_pattern.match(line)
                if match:
                    word_indices.append(idx)
                    frequencies.append(int(match.group(2)))

        total_words = len(word_indices)
        if total_words <= MAX_WORDS_LIMIT:
            print(f"[V] {file_path:.<40} OK ({total_words:,} words)")
            return

        print(f"\n{'!'*60}")
        print(f" OPTIMIZATION: {file_path}")
        print(f"{'!'*60}")

        # 1. Calculate standard threshold for the given ratio
        num_target_remove = int(total_words * TARGET_REDUCTION_RATIO)
        temp_freqs = sorted(frequencies)
        threshold_f = temp_freqs[num_target_remove]

        # 2. Check how many words would be removed at <= threshold_f
        to_remove_at_threshold = sum(1 for f in frequencies if f <= threshold_f)
        
        # 3. Apply safety limit
        limit_safety = int(total_words * SAFETY_MAX_REDUCTION)
        
        is_force_cutoff = False
        if to_remove_at_threshold > limit_safety:
            print(f" [!] WARNING: Threshold f<={threshold_f} would remove {to_remove_at_threshold:,} words.")
            print(f" [!] SAFETY LIMIT applied: Limiting removal to {SAFETY_MAX_REDUCTION*100:.0f}% of total.")
            is_force_cutoff = True
            actual_to_remove = limit_safety
        else:
            actual_to_remove = to_remove_at_threshold

        output_lines = []
        removed_actual = 0

        # REMOVAL LOGIC
        if is_force_cutoff or threshold_f <= 1:
            # Physical cutoff method from the end (keep first N words)
            words_to_keep = total_words - actual_to_remove
            last_word_idx = word_indices[words_to_keep - 1]
            
            # Find end of bigrams for the last word
            end_line_idx = last_word_idx + 1
            while end_line_idx < len(all_lines) and bigram_pattern.match(all_lines[end_line_idx]):
                end_line_idx += 1
            
            output_lines = all_lines[:end_line_idx]
            removed_actual = total_words - words_to_keep
            method = f"Physical cutoff of excess (limit {SAFETY_MAX_REDUCTION*100:.0f}%)"
        else:
            # Standard frequency filtering
            method = f"Frequency filtering (f <= {threshold_f})"
            keep = True
            for line in all_lines:
                m = word_pattern.match(line)
                if m:
                    if int(m.group(2)) <= threshold_f:
                        keep = False
                        removed_actual += 1
                    else:
                        keep = True
                        output_lines.append(line)
                    continue
                if bigram_pattern.match(line):
                    if keep: output_lines.append(line)
                    continue
                output_lines.append(line)

        print(f" -> Method:        {method}")
        print(f" -> Input words:   {total_words:,}")
        print(f" -> Removed:       {removed_actual:,} words")
        print(f" -> Remaining:     {total_words - removed_actual:,} words")

        if fix_mode:
            if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
            out_path = os.path.join(OUTPUT_FOLDER, file_path)
            with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
                f.writelines(output_lines)
            verify_fixed_file(out_path, total_words - removed_actual)
        
        print(f"{'='*60}\n")

    except Exception as e:
        print(f" [X] ERROR: {e}")

def main():
    global MAX_WORDS_LIMIT, TARGET_REDUCTION_RATIO, SAFETY_MAX_REDUCTION, OUTPUT_FOLDER

    parser = argparse.ArgumentParser(
        description="Script for optimizing and reducing the number of words in .combined dictionary files.",
        epilog="Usage examples:\n"
               "  python dictionary_filter.py --help\n"
               "  python dictionary_filter.py --fix\n"
               "  python dictionary_filter.py --fix --word-size 2000000 --reduce-size 0.35 --output-dir \"optimized\"",
        formatter_class=argparse.RawTextHelpFormatter # Allows preserving formatting (line breaks) in epilog section
    )
    
    parser.add_argument("--fix", action="store_true",
                        help="Enables write mode. If provided, modified files will be saved to disk.")

    parser.add_argument("--word-size", type=int, default=MAX_WORDS_LIMIT, metavar="X",
                        help=f"Word limit that triggers optimization. Overrides MAX_WORDS_LIMIT.\n(Default: {MAX_WORDS_LIMIT})")

    parser.add_argument("--reduce-size", type=float, default=TARGET_REDUCTION_RATIO, metavar="X",
                        help=f"Reduction ratio (e.g., 0.20 = 20%% of words removed).\nOverrides TARGET_REDUCTION_RATIO and SAFETY_MAX_REDUCTION.\n(Default: {TARGET_REDUCTION_RATIO})")

    parser.add_argument("--output-dir", type=str, default=OUTPUT_FOLDER, metavar="DIRNAME",
                        help=f"Name of the folder where output files will be saved.\nOverrides OUTPUT_FOLDER.\n(Default: '{OUTPUT_FOLDER}')")

    args = parser.parse_args()

    MAX_WORDS_LIMIT = args.word_size
    TARGET_REDUCTION_RATIO = args.reduce_size
    SAFETY_MAX_REDUCTION = args.reduce_size
    OUTPUT_FOLDER = args.output_dir

    files = [f for f in os.listdir('.') if f.endswith('.combined')]
    if not files:
        print("No .combined files found in the current directory.")
        return

    for f in files: 
        process_combined_file(f, args.fix)

if __name__ == "__main__": 
    main()