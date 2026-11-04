import csv
import json
import os
import re

import pymorphy3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "text_ru")
OUT = os.path.join(ROOT, "annotations", "text")
CORRECTIONS_PATH = os.path.join(OUT, "manual_corrections.json")
MORPH = pymorphy3.MorphAnalyzer()

TOKEN_RE = re.compile(r"[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)*|[A-Za-z]+|\d+(?:[.,]\d+)?|[^\w\s]", re.U)
LATIN_RE = re.compile(r"[A-Za-z]+$")
SENT_END = {".", "!", "?"}

UPOS = {"NOUN": "NOUN", "ADJF": "ADJ", "ADJS": "ADJ", "COMP": "ADV", "VERB": "VERB", "INFN": "VERB",
        "PRTF": "VERB", "PRTS": "VERB", "GRND": "VERB", "NUMR": "NUM", "ADVB": "ADV", "NPRO": "PRON",
        "PRED": "ADV", "PREP": "ADP", "CONJ": "CCONJ", "PRCL": "PART", "INTJ": "INTJ"}
CASE = {"nomn": "Nom", "gent": "Gen", "datv": "Dat", "accs": "Acc", "ablt": "Ins", "loct": "Loc",
        "gen2": "Gen", "acc2": "Acc", "loc2": "Loc"}
NUMBER = {"sing": "Sing", "plur": "Plur"}
GENDER = {"masc": "Masc", "femn": "Fem", "neut": "Neut"}

ENTITY_TYPES = {
    "SPECIES": "название вида птицы, в том числе латинское",
    "TAXON": "название систематической группы (птица, утка, семейство, род)",
    "SEX": "пол особи (самец, самка)",
    "NEST": "гнездо и кладка",
    "BODY_PART": "часть тела птицы",
    "COLOR": "цвет, окраска",
    "HABITAT": "среда обитания, территория распространения",
    "VOICE": "голос, звук, песня",
    "FOOD": "корм, добыча",
}

GAZETTEER = {
    "SPECIES": [("домовый", "воробей"), ("настоящий", "воробей"), ("большой", "синица"), ("серый", "ворона"),
                ("чёрный", "дрозд"), ("чёрный", "ворона"), ("западный", "соловей"), ("южный", "соловей"),
                ("восточный", "соловей"), ("деревенский", "ласточка"), ("обыкновенный", "кукушка"),
                ("белый", "аист"), ("дальневосточный", "аист"), ("обыкновенный", "сорока"),
                ("европейский", "сорока"), ("воробей",), ("синица",), ("сорока",), ("ворона",), ("дрозд",),
                ("соловей",), ("ласточка",), ("ласточка-касатка",), ("кукушка",), ("аист",), ("кряква",),
                ("большак",), ("грач",)],
    "TAXON": [("птица",), ("утка",), ("вид",), ("подвид",), ("род",), ("семейство",), ("отряд",), ("ворон",),
              ("воробьиный",), ("синицевый",), ("дроздовый",), ("мухоловковый",), ("аистовый",), ("врановый",),
              ("кукушковый",), ("утиный",), ("гусеобразный",), ("воробьинообразный",)],
    "SEX": [("самец",), ("самка",)],
    "NEST": [("гнездо",), ("кладка",), ("яйцо",)],
    "BODY_PART": [("клюв",), ("хвост",), ("оперение",), ("крыло",), ("шея",), ("голова",), ("грудь",), ("спина",),
                  ("горло",), ("щека",), ("лоб",), ("туловище",), ("нога",), ("лапка",), ("радужка",), ("глаз",),
                  ("подбородок",), ("зоб",), ("верх",), ("низ",), ("пятно",), ("пятнышко",), ("полоса",),
                  ("манишка",), ("зеркало",), ("ушной", "область"), ("ротовой", "полость")],
    "COLOR": [("окраска",), ("цвет",), ("оттенок",), ("тон",), ("ржавчинный",), ("коричневато-бурый",),
              ("голубоватый",), ("серый",), ("коричневый",), ("чёрный",), ("белый",), ("жёлтый",), ("рыжий",),
              ("синий",), ("зелёный",), ("бурый",), ("красный",), ("голубой",), ("розовый",), ("бежевый",),
              ("светлый",), ("тёмный",), ("оливковый",), ("беловатый",), ("буроватый",), ("красноватый",),
              ("коричневатый",), ("желтовато-белый",), ("серо-жёлтый",), ("тёмно-серый",), ("тёмно-бурый",),
              ("серо-коричневый",), ("серо-желтоватый",), ("сине-чёрный",), ("жёлто-розовый",),
              ("светло-коричневый",), ("бледно-бежевый",), ("бледно-серый",), ("сине-фиолетовый",),
              ("коричнево-бурый",), ("буровато-серый",), ("тёмно-коричневый",)],
    "HABITAT": [("лес",), ("водоём",), ("опушка",), ("берег",), ("город",), ("окрестность",), ("территория",),
                ("северный", "европа"), ("северный", "африка"), ("южный", "азия"), ("южный", "америка"),
                ("южный", "китай"), ("новый", "зеландия"), ("ближний", "восток"), ("дальний", "восток"),
                ("британский", "остров"), ("европа",), ("азия",), ("африка",), ("америка",), ("россия",),
                ("австралия",), ("антарктида",), ("скандинавия",), ("испания",), ("греция",), ("марокко",),
                ("алжир",), ("тунис",), ("турция",), ("иран",), ("япония",), ("сибирь",), ("китай",), ("корея",),
                ("индия",), ("непал",), ("мьянма",), ("таиланд",), ("монголия",), ("казахстан",), ("индонезия",),
                ("микронезия",), ("пиренеи",), ("гималаи",), ("персидский", "залив"), ("японский", "море"),
                ("средиземный", "море")],
    "VOICE": [("песня",), ("пение",), ("щебет",), ("трель",), ("чириканье",), ("крик",), ("голос",),
              ("щёлканье",), ("мяуканье",), ("звукоподражание",)],
    "FOOD": [("насекомое",), ("личинка",), ("беспозвоночный",), ("червь",), ("гусеница",), ("паук",),
             ("корм",)],
}

CORRECTIONS = {
    "сорока": {"upos": "NOUN", "lemma": "сорока"}, "сороки": {"upos": "NOUN", "lemma": "сорока"},
    "сорок": {"upos": "NOUN", "lemma": "сорока"}, "ворону": {"upos": "NOUN", "lemma": "ворона"},
    "вороны": {"upos": "NOUN", "lemma": "ворона"}, "вороной": {"upos": "NOUN", "lemma": "ворона"},
    "верхом": {"upos": "NOUN", "lemma": "верх"}, "низом": {"upos": "NOUN", "lemma": "низ"},
    "темнее": {"upos": "ADV", "lemma": "тёмный"}, "их": {"upos": "PRON", "lemma": "они"},
    "её": {"upos": "PRON", "lemma": "она"}, "это": {"upos": "PRON", "lemma": "это"},
    "этого": {"upos": "ADJ", "lemma": "этот"}, "этих": {"upos": "ADJ", "lemma": "этот"},
    "этот": {"upos": "ADJ", "lemma": "этот"}, "одного": {"upos": "NUM", "lemma": "один"},
    "одна": {"upos": "NUM", "lemma": "один"}, "большая": {"upos": "ADJ", "lemma": "большой"},
    "больших": {"upos": "ADJ", "lemma": "большой"}, "линнеем": {"upos": "PROPN", "lemma": "линней"},
    "хартертом": {"upos": "PROPN", "lemma": "хартерт"}, "лат": {"upos": "X", "lemma": "лат"},
    "несколько": {"upos": "ADV", "lemma": "несколько"}, "много": {"upos": "ADV", "lemma": "много"},
    "мало": {"upos": "ADV", "lemma": "мало"}, "вокруг": {"upos": "ADP", "lemma": "вокруг"},
    "см": {"upos": "NOUN", "lemma": "см"}, "белые": {"upos": "ADJ", "lemma": "белый"},
    "врановых": {"upos": "ADJ", "lemma": "врановый"}, "распространённый": {"upos": "ADJ", "lemma": "распространённый"},
    "распространённая": {"upos": "ADJ", "lemma": "распространённый"},
    "узнаваемая": {"upos": "ADJ", "lemma": "узнаваемый"},
}


def is_sentence_end(cur, tokens, idx):
    if tokens[idx] != ".":
        return True
    previous = cur[-2] if len(cur) >= 2 else ""
    if previous.lower() == "лат" or re.fullmatch(r"[А-ЯЁA-Z]", previous):
        return False
    following = tokens[idx + 1] if idx + 1 < len(tokens) else ""
    return not following or bool(re.match(r"[А-ЯЁA-Z«\"(]", following))


def tokenize(text):
    paragraphs = []
    for par in [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]:
        sents, cur = [], []
        tokens = TOKEN_RE.findall(par)
        for idx, tok in enumerate(tokens):
            cur.append(tok)
            if tok in SENT_END and is_sentence_end(cur, tokens, idx):
                sents.append(cur)
                cur = []
        if cur:
            sents.append(cur)
        paragraphs.append(sents)
    return paragraphs


def analyze(tok):
    if re.fullmatch(r"[^\w\s]", tok):
        return {"lemma": tok, "upos": "PUNCT", "feats": "_"}
    if re.fullmatch(r"\d+(?:[.,]\d+)?", tok):
        return {"lemma": tok, "upos": "NUM", "feats": "_"}
    if LATIN_RE.match(tok):
        return {"lemma": tok.lower(), "upos": "X", "feats": "Foreign=Yes"}
    p = MORPH.parse(tok)[0]
    tag = p.tag
    feats = []
    if tag.case in CASE:
        feats.append(f"Case={CASE[tag.case]}")
    if tag.gender in GENDER:
        feats.append(f"Gender={GENDER[tag.gender]}")
    if tag.number in NUMBER:
        feats.append(f"Number={NUMBER[tag.number]}")
    res = {"lemma": p.normal_form, "upos": UPOS.get(tag.POS, "X"), "feats": "|".join(sorted(feats)) or "_"}
    res.update(CORRECTIONS.get(tok.lower(), {}))
    if res["upos"] in ("X", "PUNCT"):
        res["feats"] = "_"
    return res


def tag_entities(tokens, infos):
    lemmas = [i["lemma"] for i in infos]
    patterns = sorted(((pat, typ) for typ, pats in GAZETTEER.items() for pat in pats), key=lambda x: -len(x[0]))
    tags = ["O"] * len(infos)
    for pat, typ in patterns:
        n = len(pat)
        for s in range(len(lemmas) - n + 1):
            if tuple(lemmas[s:s + n]) == pat and all(t == "O" for t in tags[s:s + n]):
                tags[s] = f"B-{typ}"
                for k in range(s + 1, s + n):
                    tags[k] = f"I-{typ}"
    i = 0
    while i < len(tokens):
        if tags[i] == "O" and LATIN_RE.match(tokens[i]):
            j = i
            while j + 1 < len(tokens) and tags[j + 1] == "O" and LATIN_RE.match(tokens[j + 1]):
                j += 1
            typ = "TAXON" if j == i or re.search(r"(idae|formes)$", tokens[i]) else "SPECIES"
            tags[i] = f"B-{typ}"
            for k in range(i + 1, j + 1):
                tags[k] = f"I-{typ}"
            i = j
        i += 1
    return tags


def load_corrections():
    if os.path.exists(CORRECTIONS_PATH):
        with open(CORRECTIONS_PATH, encoding="utf-8") as f:
            return {(c["doc"], c["sent"], c["idx"]): c for c in json.load(f)}
    return {}


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(ROOT, "metadata", "species.csv"), encoding="utf-8") as f:
        species = {r["slug"]: r for r in csv.DictReader(f)}
    fixes = load_corrections()
    all_rows, ent_rows = [], []
    for slug in species:
        with open(os.path.join(SRC, f"{slug}.txt"), encoding="utf-8") as f:
            text = f.read()
        lines = [f"# newdoc id = {slug}", f"# species = {species[slug]['scientific_name']}"]
        sent_no = 0
        for pi, par in enumerate(tokenize(text), 1):
            lines.append(f"# newpar id = {slug}-p{pi}")
            for sent in par:
                sent_no += 1
                infos = [analyze(t) for t in sent]
                for i, (t, inf) in enumerate(zip(sent, infos)):
                    if i > 0 and inf["upos"] == "NOUN" and t[0].isupper():
                        inf["upos"] = "PROPN"
                tags = tag_entities(sent, infos)
                for i in range(len(sent)):
                    fix = fixes.get((slug, sent_no, i + 1))
                    if fix:
                        if fix["token"] != sent[i]:
                            raise ValueError(f"исправление не совпадает с токеном: {fix}")
                        tags[i] = fix.get("ner", tags[i])
                        for key in ("lemma", "upos"):
                            if key in fix:
                                infos[i][key] = fix[key]
                lines.append(f"# sent_id = {slug}-s{sent_no}")
                plain = re.sub(r" ([.,!?;:»)])", r"\1", " ".join(sent))
                lines.append("# text = " + re.sub(r"([«(]) ", r"\1", plain))
                for i, (t, inf, tag) in enumerate(zip(sent, infos, tags), 1):
                    misc = [] if tag == "O" else [f"NER={tag}"]
                    if i < len(sent) and re.fullmatch(r"[.,!?;:»)]", sent[i]):
                        misc.append("SpaceAfter=No")
                    lines.append("\t".join([str(i), t, inf["lemma"], inf["upos"], "_", inf["feats"], "_", "_", "_",
                                            "|".join(misc) or "_"]))
                    all_rows.append(dict(doc=slug, par=pi, sent=sent_no, idx=i, token=t, lemma=inf["lemma"],
                                         upos=inf["upos"], ner=tag))
                lines.append("")
                cur = None
                for i, (t, tag) in enumerate(zip(sent, tags)):
                    if tag.startswith("B-"):
                        cur = dict(doc=slug, par=pi, sent=sent_no, type=tag[2:], text=t, lemma=infos[i]["lemma"])
                        ent_rows.append(cur)
                    elif tag.startswith("I-") and cur:
                        cur["text"] += " " + t
                        cur["lemma"] += " " + infos[i]["lemma"]
                    else:
                        cur = None
        with open(os.path.join(OUT, f"{slug}.conllu"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    for name, rows in [("all_tokens.tsv", all_rows), ("entities.csv", ent_rows)]:
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t" if name.endswith("tsv") else ",")
            w.writeheader()
            w.writerows(rows)
    with open(os.path.join(OUT, "entity_types.json"), "w", encoding="utf-8") as f:
        json.dump(ENTITY_TYPES, f, ensure_ascii=False, indent=2)
    print(f"Документов: {len(species)}, токенов: {len(all_rows)}, сущностей: {len(ent_rows)}")


if __name__ == "__main__":
    main()
