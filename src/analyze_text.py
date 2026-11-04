import html
import itertools
import os

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "annotations", "text")
COLORS = {"SPECIES": "#f4b183", "TAXON": "#fbe5d6", "BODY_PART": "#9dc3e6", "COLOR": "#ffe699", "HABITAT": "#a9d18e",
          "VOICE": "#d5a6bd", "FOOD": "#c9c9c9", "SEX": "#b4a7d6", "NEST": "#a2c4c9"}
POS_NAMES = {"NOUN": "существительные", "ADJ": "прилагательные", "PROPN": "имена собственные",
             "X": "латинские слова", "ADV": "наречия", "ADP": "предлоги", "PUNCT": "знаки препинания"}
plt.rcParams["font.family"] = "DejaVu Sans"

tok = pd.read_csv(os.path.join(OUT, "all_tokens.tsv"), sep="\t")
ent = pd.read_csv(os.path.join(OUT, "entities.csv"))
tok["etype"] = tok["ner"].str.replace(r"^[BI]-", "", regex=True)


def build_html():
    parts = ["<html><head><meta charset='utf-8'><title>Разметка текстов о птицах</title><style>"
             "body{font-family:sans-serif;max-width:900px;margin:20px auto;line-height:2}"
             "span.e{padding:2px 4px;border-radius:4px;margin:0 1px}small{color:#555;font-size:9px;margin-left:2px}"
             "h3{margin-top:30px}</style></head><body>",
             "<h2>Разметка текстов: сущности и части речи</h2><p>" +
             " ".join(f"<span class='e' style='background:{c}'>{t}</span>" for t, c in COLORS.items()) + "</p>"]
    for doc, g in tok.groupby("doc", sort=False):
        parts.append(f"<h3>{doc}</h3>")
        for _, s in g.groupby("sent", sort=False):
            out, i, rows = [], 0, s.to_dict("records")
            while i < len(rows):
                r = rows[i]
                if r["ner"].startswith("B-"):
                    j = i + 1
                    while j < len(rows) and rows[j]["ner"].startswith("I-"):
                        j += 1
                    txt = " ".join(x["token"] for x in rows[i:j])
                    out.append(f"<span class='e' style='background:{COLORS.get(r['etype'], '#ddd')}' "
                               f"title='{r['etype']}'>{html.escape(txt)}<small>{r['etype']}</small></span>")
                    i = j
                else:
                    out.append(f"<span title='{r['upos']}'>{html.escape(r['token'])}</span>")
                    i += 1
            parts.append("<div>" + " ".join(out) + "</div>")
    parts.append("</body></html>")
    with open(os.path.join(OUT, "annotation_view.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def build_plots(share):
    cnt = ent.groupby(["doc", "type"]).size().unstack(fill_value=0)
    ax = cnt.plot(kind="bar", stacked=True, figsize=(11, 5), color=[COLORS.get(c, "#ddd") for c in cnt.columns],
                  edgecolor="#555", linewidth=.4)
    ax.set_title("Именованные сущности по текстам и типам")
    ax.set_xlabel("")
    ax.set_ylabel("число сущностей")
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", title="тип")
    plt.xticks(rotation=40, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "stats_entities.png"), dpi=130)
    plt.close()
    ax = share.plot(kind="bar", stacked=True, figsize=(10, 5), edgecolor="#555", linewidth=.4)
    ax.set_title("Части речи внутри сущностей (доля токенов)")
    ax.set_xlabel("")
    ax.set_ylabel("доля")
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", title="часть речи")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "stats_pos_by_entity.png"), dpi=130)
    plt.close()


def pct(a, b):
    return round(100 * a / b) if b else 0


def main():
    build_html()
    inside = tok[tok["etype"] != "O"]
    pos_by = inside.groupby(["etype", "upos"]).size().unstack(fill_value=0)
    share = pos_by.div(pos_by.sum(axis=1), axis=0)
    build_plots(share)

    sent_types = ent.groupby(["doc", "sent"])["type"].apply(lambda x: sorted(set(x)))
    n_sent = tok.groupby(["doc", "sent"]).ngroups
    types = sorted(COLORS)
    co = pd.DataFrame(0, index=types, columns=types)
    for ts in sent_types:
        for a, b in itertools.combinations(ts, 2):
            co.loc[a, b] += 1
            co.loc[b, a] += 1

    pairs = {}
    for _, s in tok.groupby(["doc", "sent"], sort=False):
        r = s.to_dict("records")
        for a, b in zip(r, r[1:]):
            if a["etype"] == "COLOR" and b["etype"] == "BODY_PART":
                key = (a["token"].lower(), b["token"].lower())
                pairs[key] = pairs.get(key, 0) + 1
    n_color = int((ent["type"] == "COLOR").sum())
    n_pairs = sum(pairs.values())
    top_pairs = ", ".join(f"«{a} {b}»" for (a, b), _ in sorted(pairs.items(), key=lambda x: -x[1])[:5])

    named = {"SPECIES", "TAXON"}

    def with_named(t):
        sel = sent_types[sent_types.apply(lambda x: t in x)]
        return len(sel), int(sel.apply(lambda x: bool(named & set(x))).sum())

    rows = ["| Тип | Преобладающая часть речи | Доля, % |", "|---|---|---|"]
    for t in share.index:
        top = share.loc[t].idxmax()
        rows.append(f"| {t} | {POS_NAMES.get(top, top)} ({top}) | {pct(share.loc[t, top], 1)} |")

    co_pairs = sorted(((co.loc[a, b], a, b) for a, b in itertools.combinations(types, 2)
                       if not ({a, b} & named)), reverse=True)[:3]
    co_text = "; ".join(f"{a} и {b} ({n})" for n, a, b in co_pairs)
    noun_types = ", ".join(t for t in share.index if share.loc[t, "NOUN"] >= 0.9)

    n_latin = int(((ent["type"] == "SPECIES") & ent["text"].str.contains(r"[A-Za-z]")).sum())
    n_species = int((ent["type"] == "SPECIES").sum())
    n_taxon = int((ent["type"] == "TAXON").sum())
    feature_sents = sent_types[sent_types.apply(lambda x: bool({"COLOR", "BODY_PART", "VOICE", "FOOD", "SEX"} & set(x)))]
    no_name = int(feature_sents.apply(lambda x: not (named & set(x))).sum())
    habitat_n, habitat_named = with_named("HABITAT")
    voice_n, voice_named = with_named("VOICE")
    sex_sent = sent_types[sent_types.apply(lambda x: "SEX" in x)]
    sex_look = int(sex_sent.apply(lambda x: bool({"COLOR", "BODY_PART"} & set(x))).sum())
    habitat_prop = pct(share.loc["HABITAT", "PROPN"], 1) if "PROPN" in share.columns else 0

    report = f"""# Анализ разметки текстов

Объём: {tok['doc'].nunique()} текстов, {len(tok)} токенов, {n_sent} предложений, {len(ent)} сущностей.

## 1. Распределение сущностей

{ent['type'].value_counts().to_frame('число').to_markdown()}

## 2. Связь частей речи и типов сущностей

{chr(10).join(rows)}

- Сущности {noun_types} состоят из существительных не менее чем на 90 %: по части речи можно предварительно отбирать кандидатов в эти типы.
- Тип COLOR содержит {pct(share.loc['COLOR', 'ADJ'], 1)} % прилагательных; остальная часть приходится на существительные («окраска», «цвет», «тон», «оттенок»).
- HABITAT на {habitat_prop} % состоит из имён собственных (географические названия), поэтому для него полезен словарь топонимов.
- Тип SPECIES неоднороден: {pct(share.loc['SPECIES', 'ADJ'], 1)} % ADJ, {pct(share.loc['SPECIES', 'NOUN'], 1)} % NOUN и {pct(share.loc['SPECIES', 'X'], 1)} % латинских слов. Названия вида на русском языке двусловные («серая ворона»), латинские записываются биномиальной номенклатурой, поэтому границы сущности нельзя определять только по части речи.

## 3. Зависимости между сущностями

- Признаки внешности связаны между собой: COLOR встречается вместе с BODY_PART в {int(co.loc['COLOR', 'BODY_PART'])} предложениях, при этом в {n_pairs} из {n_color} случаев ({pct(n_pairs, n_color)} %) COLOR стоит непосредственно перед BODY_PART (примеры: {top_pairs}).
- Чаще всего в одном предложении встречаются (число предложений): {co_text}.
- Пол связан с описанием внешности: {sex_look} из {len(sex_sent)} предложений с SEX содержат COLOR или BODY_PART.
- Название вида или группы (SPECIES/TAXON) есть в {voice_named} из {voice_n} предложений с VOICE и в {habitat_named} из {habitat_n} предложений с HABITAT.
- В {no_name} из {len(feature_sents)} предложений с признаками (COLOR, BODY_PART, VOICE, FOOD, SEX) нет названия вида или группы (SPECIES, TAXON).
- Объём выборки ограничен ({len(tok)} токенов, {tok['doc'].nunique()} текстов), поэтому выводы относятся к данному корпусу.

Матрица совместной встречаемости типов в предложении:

{co.to_markdown()}

## 4. Предложения по обновлению схемы

1. Добавить уровень отношений между сущностями: `hasColor` (BODY_PART → COLOR), `hasVoice` (SPECIES → VOICE), `livesIn` (SPECIES → HABITAT), `eats` (SPECIES → FOOD), `hasSex` (SPECIES → SEX).
2. Строить отношения на уровне абзаца, а не предложения: в {pct(no_name, len(feature_sents))} % предложений с признаками нет названия вида или группы.
3. Отделить латинские названия от русских: они составляют {pct(n_latin, n_species)} % сущностей SPECIES ({n_latin} из {n_species}) и связываются с видом через поле `species` в `metadata/species.csv`.
4. Учитывать TAXON отдельно от SPECIES: сущностей TAXON {n_taxon}, это {pct(n_taxon, len(ent))} % всех, но они описывают систематику, а не конкретный вид.
5. Для HABITAT использовать словарь топонимов (в сущностях преобладают имена собственные).
"""
    with open(os.path.join(OUT, "analysis_report.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print("Сохранено:", os.path.join(OUT, "analysis_report.md"))


if __name__ == "__main__":
    main()
