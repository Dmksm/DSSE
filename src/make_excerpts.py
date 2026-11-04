import csv
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_WORDS, MAX_WORDS = 120, 130
ABBREVIATIONS = {"г", "гг", "т", "е", "д", "п", "см", "рис", "им", "ок", "др", "тыс", "лат", "англ", "мм", "кг",
                 "км", "ч", "в", "вв", "н", "э", "г.", "руб", "млн", "ср"}


def russian_part(text):
    marker = re.search(r"^## .*$", text, flags=re.M)
    body = text[marker.end():] if marker else text
    lines = body.splitlines()
    lines = [l.strip() for l in lines if l.strip() and not l.startswith("Источник:") and not re.match(r"^=+ .* =+$", l.strip())]
    return " ".join(lines)


def split_sentences(text):
    text = text.replace("́", "")
    parts, start = [], 0
    for m in re.finditer(r"[.!?]+(?=\s+[А-ЯЁA-Z\"«])", text):
        before = text[start:m.start()].split()
        if before and before[-1].lower().strip("(«\"") in ABBREVIATIONS:
            continue
        parts.append(text[start:m.end()].strip())
        start = m.end()
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def excerpt(sentences):
    chosen, words = [], 0
    for s in sentences:
        n = len(s.split())
        if words + n > MAX_WORDS:
            if words >= MIN_WORDS:
                break
            continue
        chosen.append(s)
        words += n
        if words >= MIN_WORDS:
            break
    return chosen, words


def main():
    with open(os.path.join(ROOT, "metadata", "species.csv"), encoding="utf-8") as f:
        species = list(csv.DictReader(f))
    out_dir = os.path.join(ROOT, "data", "text_ru")
    os.makedirs(out_dir, exist_ok=True)
    for sp in species:
        with open(os.path.join(ROOT, "data", "text", f"{sp['slug']}.txt"), encoding="utf-8") as f:
            text = f.read()
        sentences, words = excerpt(split_sentences(russian_part(text)))
        with open(os.path.join(out_dir, f"{sp['slug']}.txt"), "w", encoding="utf-8") as f:
            f.write(" ".join(sentences) + "\n")
        print(f"{sp['slug']}: {len(sentences)} предложений, {words} слов")


if __name__ == "__main__":
    main()
