import os
import sys

import pandas as pd
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_EXT = {".ogg", ".oga", ".mp3", ".wav", ".flac"}
MODALITIES = ["text", "image", "audio"]


def main():
    species = pd.read_csv(os.path.join(ROOT, "metadata", "species.csv"))
    man = pd.read_csv(os.path.join(ROOT, "metadata", "manifest.csv"))
    problems = []
    for _, r in man.iterrows():
        p = os.path.join(ROOT, r["file"])
        if not os.path.isfile(p) or os.path.getsize(p) == 0:
            problems.append(f"нет файла или он пустой: {r['file']}")
            continue
        if r["modality"] == "image":
            try:
                with Image.open(p) as im:
                    im.verify()
            except Exception as e:
                problems.append(f"битое изображение {r['file']}: {e}")
        elif r["modality"] == "audio" and os.path.splitext(p)[1].lower() not in AUDIO_EXT:
            problems.append(f"неожиданный формат аудио: {r['file']}")
        elif r["modality"] == "text" and os.path.getsize(p) < 200:
            problems.append(f"слишком короткий текст: {r['file']}")

    known = set(man["file"])
    for folder in ["text", "images", "audio"]:
        base = os.path.join(ROOT, "data", folder)
        for dirpath, _, names in os.walk(base):
            for name in names:
                rel = os.path.relpath(os.path.join(dirpath, name), ROOT).replace(os.sep, "/")
                if name != ".gitkeep" and rel not in known:
                    problems.append(f"файл не описан в manifest.csv: {rel}")

    table = man.pivot_table(index="species", columns="modality", values="file", aggfunc="count", fill_value=0)
    for m in MODALITIES:
        if m not in table:
            table[m] = 0
    table = table.reindex(species["slug"]).fillna(0).astype(int)[MODALITIES]
    for slug, row in table.iterrows():
        for m in MODALITIES:
            if row[m] == 0:
                problems.append(f"{slug}: нет данных модальности {m}")
    print(table.to_string())
    print("\nВсего файлов:", len(man), "| видов:", len(species))
    print("Проблем не найдено." if not problems else "ПРОБЛЕМЫ:\n - " + "\n - ".join(problems))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
