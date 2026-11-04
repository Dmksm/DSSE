import argparse
import csv
import html
import os
import re
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADERS = {"User-Agent": "dsse-bird-dataset/1.0 (https://github.com/Dmksm)"}
WIKI = "https://{lang}.wikipedia.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
DELAY = 2.5
SERVICE_SECTIONS = (r"\n=+ (?:References|See also|Notes|External links|Further reading|Sources|Bibliography|"
                    r"Примечания|Литература|Ссылки|См\. также|Источники|Комментарии) =+")
FIELDS = ["file", "modality", "species", "source_url", "license", "author", "lang"]


def http_get(url, retries=6, **kw):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60, **kw)
        except requests.RequestException as e:
            print(f"  сеть: {e}; повтор {attempt + 1}/{retries}", flush=True)
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code in (429, 500, 502, 503, 504):
            wait = min(int(r.headers.get("Retry-After", 0) or 0) or 30 * (attempt + 1), 180)
            print(f"  HTTP {r.status_code}; пауза {wait} с, повтор {attempt + 1}/{retries}; {r.url[:120]}", flush=True)
            time.sleep(wait)
            continue
        r.raise_for_status()
        time.sleep(DELAY)
        return r
    raise RuntimeError(f"запрос не выполнен: {url}")


def api(url, **params):
    params.update(format="json", formatversion=2)
    return http_get(url, params=params).json()


def clean(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", value or ""))).strip()


def norm(value):
    return re.sub(r"[_\s]+", " ", value).lower()


def get_extract(lang, title):
    d = api(WIKI.format(lang=lang), action="query", prop="extracts|info|langlinks", inprop="url",
            titles=title, explaintext=1, redirects=1, lllang="ru", lllimit=1)
    page = d["query"]["pages"][0]
    if page.get("missing"):
        return None
    text = re.split(SERVICE_SECTIONS, page.get("extract") or "")[0]
    text = re.sub(r"\s*\(\s*\)", "", text).strip()
    return {"url": page.get("fullurl", ""), "text": text, "ru_title": (page.get("langlinks") or [{}])[0].get("title")}


def collect_text(sp):
    en = get_extract("en", sp["wikipedia_title"])
    if not en or not en["text"]:
        return []
    parts = [f"# {sp['english_name']} ({sp['scientific_name']})", f"Источник: {en['url']} (CC BY-SA 4.0)", "", en["text"]]
    row = dict(file=f"data/text/{sp['slug']}.txt", modality="text", species=sp["slug"], source_url=en["url"],
               license="CC BY-SA 4.0", author="Авторы Википедии", lang="en")
    if en["ru_title"]:
        ru = get_extract("ru", en["ru_title"])
        if ru and ru["text"]:
            parts += ["", f"## {sp['russian_name']}", f"Источник: {ru['url']} (CC BY-SA 4.0)", "", ru["text"]]
            row["lang"] = "en+ru"
    path = os.path.join(ROOT, row["file"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return [row]


def commons_search(query, limit, thumb_width=None):
    params = dict(action="query", generator="search", gsrsearch=query, gsrnamespace=6, gsrlimit=limit,
                  prop="imageinfo", iiprop="url|mime|extmetadata|size")
    if thumb_width:
        params["iiurlwidth"] = thumb_width
    d = api(COMMONS, **params)
    pages = sorted(d.get("query", {}).get("pages", []), key=lambda p: p.get("index", 0))
    return [p for p in pages if p.get("imageinfo")]


def meta(info, key):
    return clean(info.get("extmetadata", {}).get(key, {}).get("value", ""))


def author(info):
    value = meta(info, "Artist")
    if not value or value.lower().startswith("unknown"):
        return "не указан"
    return value[:100]


def relevant(sp, modality, page, info):
    title = norm(page["title"])
    sci = sp["scientific_name"].lower()
    if modality == "audio":
        if re.match(r"^file:[a-z]{2,3}([- ][a-z]{2})?[- ]", title):
            return False
        return sci in title or sp["english_name"].lower() in title
    return sci in title or sp["english_name"].lower() in title or sci in norm(meta(info, "Categories"))


def recording_key(title):
    m = re.search(r"XC\d+", title)
    return m.group(0) if m else title


def download(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(http_get(url).content)


def collect_commons(sp, modality, n):
    exts = {"image": {"image/jpeg": ".jpg", "image/png": ".png"},
            "audio": {"audio/ogg": ".ogg", "application/ogg": ".ogg", "audio/mpeg": ".mp3",
                      "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/flac": ".flac"}}[modality]
    folder = "images" if modality == "image" else "audio"
    sci, eng = sp["scientific_name"], sp["english_name"]
    if modality == "image":
        queries = [(f'"{sci}" filetype:bitmap', 960), (f'"{eng}" filetype:bitmap', 960)]
    else:
        queries = [(f'"{sci}" filetype:audio', None), (f'{sci} XC filetype:audio', None), (f'"{eng}" filetype:audio', None)]
    rows, seen = [], set()
    for query, thumb in queries:
        if len(rows) >= n:
            break
        for page in commons_search(query, limit=max(n * 6, 20), thumb_width=thumb):
            if len(rows) >= n:
                break
            key = recording_key(page["title"])
            if key in seen:
                continue
            info = page["imageinfo"][0]
            ext = exts.get(info.get("mime"))
            lic = meta(info, "LicenseShortName")
            if not ext or not lic or not relevant(sp, modality, page, info):
                continue
            rel = f"data/{folder}/{sp['slug']}/{sp['slug']}_{len(rows) + 1:02d}{ext}"
            try:
                download(info.get("thumburl") or info["url"], os.path.join(ROOT, rel))
            except Exception:
                continue
            seen.add(key)
            print(f"  {rel}", flush=True)
            rows.append(dict(file=rel, modality=modality, species=sp["slug"],
                             source_url=info.get("descriptionurl", info["url"]),
                             license=lic, author=author(info), lang=""))
    return rows


def clear(sp, modality):
    if modality == "text":
        path = os.path.join(ROOT, "data", "text", f"{sp['slug']}.txt")
        if os.path.isfile(path):
            os.remove(path)
        return
    folder = os.path.join(ROOT, "data", "images" if modality == "image" else "audio", sp["slug"])
    if os.path.isdir(folder):
        for name in os.listdir(folder):
            if name != ".gitkeep":
                os.remove(os.path.join(folder, name))


def save(manifest, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(manifest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", type=int, default=3)
    ap.add_argument("--audio", type=int, default=2)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    with open(os.path.join(ROOT, "metadata", "species.csv"), encoding="utf-8") as f:
        species = list(csv.DictReader(f))

    manifest_path = os.path.join(ROOT, "metadata", "manifest.csv")
    manifest = []
    if os.path.exists(manifest_path) and not args.force:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = [r for r in csv.DictReader(f) if os.path.isfile(os.path.join(ROOT, r["file"]))]

    need = {"text": 1, "image": args.images, "audio": args.audio}
    fetch = {"text": collect_text,
             "image": lambda s: collect_commons(s, "image", args.images),
             "audio": lambda s: collect_commons(s, "audio", args.audio)}
    for sp in species:
        print(f"{sp['english_name']} ({sp['scientific_name']})")
        for modality in ["text", "image", "audio"]:
            have = [r for r in manifest if r["species"] == sp["slug"] and r["modality"] == modality]
            if len(have) >= need[modality]:
                continue
            manifest = [r for r in manifest if not (r["species"] == sp["slug"] and r["modality"] == modality)]
            clear(sp, modality)
            try:
                rows = fetch[modality](sp)
            except Exception as e:
                print(f"  {modality}: ошибка {e}")
                rows = []
            print(f"  {modality}: {len(rows)}")
            manifest += rows
            save(manifest, manifest_path)
    save(manifest, manifest_path)
    print(f"Записей в manifest.csv: {len(manifest)}")


if __name__ == "__main__":
    main()
