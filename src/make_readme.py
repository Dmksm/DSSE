import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
START, END = "<!-- AUTO:START -->", "<!-- AUTO:END -->"
SKIP = {".git", "__pycache__", ".ipynb_checkpoints", ".venv", "venv"}


def tree(path, prefix="", depth=0):
    lines = []
    entries = sorted(e for e in os.listdir(path) if e not in SKIP)
    dirs = [e for e in entries if os.path.isdir(os.path.join(path, e))]
    files = [e for e in entries if not os.path.isdir(os.path.join(path, e)) and e != ".gitkeep"]
    items = dirs + files
    for i, name in enumerate(items):
        last = i == len(items) - 1
        full = os.path.join(path, name)
        lines.append(f"{prefix}{'└── ' if last else '├── '}{name}{'/' if os.path.isdir(full) else ''}")
        if os.path.isdir(full):
            sub = [e for e in os.listdir(full) if e != ".gitkeep"]
            if depth >= 2 and all(not os.path.isdir(os.path.join(full, e)) for e in sub):
                lines[-1] += f"  [{len(sub)}]"
            else:
                lines += tree(full, prefix + ("    " if last else "│   "), depth + 1)
    return lines


def main():
    species = pd.read_csv(os.path.join(ROOT, "metadata", "species.csv"))
    man = pd.read_csv(os.path.join(ROOT, "metadata", "manifest.csv"))
    cnt = man.pivot_table(index="species", columns="modality", values="file", aggfunc="count", fill_value=0)
    for m in ["text", "image", "audio"]:
        if m not in cnt:
            cnt[m] = 0
    cnt = cnt.reindex(species["slug"]).fillna(0).astype(int)

    rows = ["| Вид | Научное название | Текст | Изображения | Аудио |", "|---|---|---|---|---|"]
    for _, s in species.iterrows():
        c = cnt.loc[s["slug"]]
        rows.append(f"| {s['russian_name']} (`{s['slug']}`) | *{s['scientific_name']}* | {c['text']} | {c['image']} | {c['audio']} |")
    rows.append(f"| **Итого** | | {cnt['text'].sum()} | {cnt['image'].sum()} | {cnt['audio'].sum()} |")
    licenses = ", ".join(f"{k} — {v}" for k, v in man["license"].value_counts().items())

    block = "\n".join([START, "", "## Структура репозитория", "", "```", "DSSE/", *tree(ROOT), "```", "",
                       "## Состав набора данных", "", *rows, "", f"Лицензии файлов: {licenses}.", "", END])
    text = open(README, encoding="utf-8").read()
    text = text[:text.index(START)] + block + text[text.index(END) + len(END):]
    with open(README, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
