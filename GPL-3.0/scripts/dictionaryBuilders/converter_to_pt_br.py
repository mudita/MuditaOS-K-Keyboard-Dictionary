#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import argparse
import io

# ===== UTF-8 FIX =====

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ===== CONFIG =====

MIN_KEY_LENGTH = 5

# ===== CACHE =====

CACHE = {}

# ===== BLACKLIST =====

BLOCKED_WORDS = {
    "seco", "seca", "secos", "secas",
    "aces", "traco", "tracos",
}

# ===== PROTECTED ROOTS =====

PROTECTED_ROOTS = {
    "activ","bacter","cact","capt","compact","conect","duct","fract",
    "hect","impact","intact","lact","pact","product","react","strict",
    "struct","tract","vector","apt","concept","script","egypt","erupt",
    "optic","recept","rupt","sept",
}

# ===== LEXICAL (SAFE ONLY) =====

LEXICAL_SAFE = {
    "autocarro": "ônibus",
    "autocarros": "ônibus",
    "comboio": "trem",
    "comboios": "trens",
    "telemóvel": "celular",
    "telemóveis": "celulares",
    "ecrã": "tela",
    "ecrãs": "telas",
    "frigorífico": "geladeira",
    "frigoríficos": "geladeiras",
    "sumo": "suco",
    "sumos": "sucos",
    "chávena": "xícara",
    "chávenas": "xícaras",
    "rebuçado": "bala",
    "rebuçados": "balas",
    "multibanco": "caixa eletrônico",
}

# ===== LEXICAL (AGGRESSIVE) =====

LEXICAL_AGGRESSIVE = {
    "rapaz": "garoto",
    "rapazes": "garotos",
    "rapariga": "moça",
    "raparigas": "moças",
    "miúdo": "menino",
    "miúda": "menina",
    "miúdos": "meninos",
    "fixe": "legal",
    "giro": "legal",
    "gira": "legal",
}

# ===== ORTHOGRAPHIC =====

ORTHO = {
    "facto": "fato",
    "factos": "fatos",
    "contacto": "contato",
    "contactos": "contatos",
    "projecto": "projeto",
    "projectos": "projetos",
    "arquitecto": "arquiteto",
    "arquitectos": "arquitetos",
    "director": "diretor",
    "directores": "diretores",
    "actor": "ator",
    "actores": "atores",
    "objecto": "objeto",
    "objectos": "objetos",
    "óptimo": "ótimo",
    "optimização": "otimização",
    "baptismo": "batismo",
    "baptista": "batista",
    "insecto": "inseto",
    "insectos": "insetos",
    "tecto": "teto",
    "tectos": "tetos",
}

# ===== HELPERS =====

def is_protected(word):
    w = word.lower()
    return any(root in w for root in PROTECTED_ROOTS)

def preserve_case(original, new):
    if original.isupper():
        return new.upper()
    if original[0].isupper():
        return new.capitalize()
    return new

def is_suspicious(old, new):
    if abs(len(old) - len(new)) > 3:
        return True
    if old[0].lower() != new[0].lower():
        return True
    return False

# ===== CORE =====

def fix_word(word, aggressive=False):
    if word in CACHE:
        return CACHE[word]

    if len(word) < 2:
        return word

    w = word.lower()

    if len(w) < MIN_KEY_LENGTH:
        return word

    if w in BLOCKED_WORDS:
        return word

    if any(c.isupper() for c in word[1:]):
        return word

    # ORTHO
    if w in ORTHO:
        new = preserve_case(word, ORTHO[w])
        if not is_suspicious(word, new):
            CACHE[word] = new
            return new

    # LEXICAL SAFE
    if w in LEXICAL_SAFE:
        new = preserve_case(word, LEXICAL_SAFE[w])
        CACHE[word] = new
        return new

    # LEXICAL AGGRESSIVE
    if aggressive and w in LEXICAL_AGGRESSIVE:
        new = preserve_case(word, LEXICAL_AGGRESSIVE[w])
        CACHE[word] = new
        return new

    CACHE[word] = word
    return word


def process_line(line, aggressive):
    match = re.match(r'^(\s*)(word=|bigram=)([^,]+)(,.*)$', line, re.DOTALL)
    if match:
        prefix, key, word, suffix = match.groups()
        fixed = fix_word(word, aggressive)
        if fixed != word:
            return True, f"{prefix}{key}{fixed}{suffix}", word, fixed

    return False, line, None, None

def update_header(line):
    return line.replace("pt_PT", "pt_BR").replace("pt_pt", "pt_br")

def main(path, fix=False, aggressive=False):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    out = []
    changes = 0

    for i, line in enumerate(lines, 1):
        if i == 1:
            line = update_header(line)

        changed, new_line, old, new = process_line(line, aggressive)

        if changed:
            changes += 1
            if not fix:
                print(f"[{i}] {old} → {new}")

        out.append(new_line)

    if fix:
        out_file = path.replace("pt_PT", "pt_BR") + ".fixed"
        with open(out_file, "w", encoding="utf-8") as f:
            f.writelines(out)
        print(f"\n✅ Saved: {out_file}")
        print(f"Changes: {changes}")
    else:
        print(f"\n🔍 Changes to be made: {changes}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--aggressive", action="store_true")
    args = p.parse_args()

    main(args.file, args.fix, args.aggressive)