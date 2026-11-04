import argparse
import sys
from xml.etree import ElementTree as ET

from image_schema import ATTRIBUTES, MIN_BOX, load_species


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


def load(path):
    data = {}
    for im in ET.parse(path).getroot().iter("image"):
        boxes = []
        for b in im.iter("box"):
            boxes.append(dict(label=b.get("label"),
                              box=tuple(float(b.get(k)) for k in ("xtl", "ytl", "xbr", "ybr")),
                              attrs={a.get("name"): (a.text or "").strip() for a in b.iter("attribute")}))
        data[im.get("name")] = dict(w=float(im.get("width")), h=float(im.get("height")), boxes=boxes)
    return data


def validate(path):
    species = {s["slug"] for s in load_species()}
    data, problems = load(path), []
    for name, im in data.items():
        if not im["boxes"]:
            problems.append(f"{name}: нет рамок")
        for i, b in enumerate(im["boxes"]):
            x1, y1, x2, y2 = b["box"]
            if b["label"] not in species:
                problems.append(f"{name}#{i}: неизвестная метка {b['label']}")
            if x1 < 0 or y1 < 0 or x2 > im["w"] + 0.5 or y2 > im["h"] + 0.5:
                problems.append(f"{name}#{i}: рамка выходит за границы изображения")
            if x2 - x1 < MIN_BOX or y2 - y1 < MIN_BOX:
                problems.append(f"{name}#{i}: рамка меньше {MIN_BOX} px")
            for n, v in b["attrs"].items():
                if n not in ATTRIBUTES or v not in ATTRIBUTES[n][0]:
                    problems.append(f"{name}#{i}: недопустимый атрибут {n}={v}")
            for j in range(i):
                if iou(b["box"], im["boxes"][j]["box"]) > 0.9:
                    problems.append(f"{name}: рамки #{j} и #{i} почти совпадают")
        folder = name.split("/")[0]
        if im["boxes"] and any(b["label"] != folder for b in im["boxes"]):
            problems.append(f"{name}: метка не совпадает с папкой вида")
    return data, problems


def compare(a_path, b_path):
    A, B = load(a_path), load(b_path)
    ious, label_ok, attr_tot, attr_ok, unmatched = [], 0, 0, 0, 0
    for name in sorted(set(A) & set(B)):
        used = set()
        for ba in A[name]["boxes"]:
            best, bj = 0, None
            for j, bb in enumerate(B[name]["boxes"]):
                v = iou(ba["box"], bb["box"])
                if j not in used and v > best:
                    best, bj = v, j
            if best >= 0.5:
                used.add(bj)
                bb = B[name]["boxes"][bj]
                ious.append(best)
                label_ok += ba["label"] == bb["label"]
                for n in ATTRIBUTES:
                    attr_tot += 1
                    attr_ok += ba["attrs"].get(n) == bb["attrs"].get(n)
            else:
                unmatched += 1
        unmatched += len(B[name]["boxes"]) - len(used)
    n = len(ious)
    return dict(matched=n, unmatched=unmatched, mean_iou=sum(ious) / n if n else 0.0,
                label_agreement=label_ok / n if n else 0.0, attr_agreement=attr_ok / attr_tot if attr_tot else 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xml")
    ap.add_argument("--compare")
    args = ap.parse_args()
    data, problems = validate(args.xml)
    names = sorted(data)
    print(f"изображений: {len(names)}, рамок: {sum(len(v['boxes']) for v in data.values())}")
    print("выборка для ручной проверки (каждое 5-е изображение):", names[4::5])
    print("Проблем не найдено." if not problems else "ПРОБЛЕМЫ:\n - " + "\n - ".join(problems))
    if args.compare:
        r = compare(args.xml, args.compare)
        print(f"\nСравнение с {args.compare}: сопоставлено рамок {r['matched']}, без пары {r['unmatched']}, "
              f"средний IoU {r['mean_iou']:.2f}, согласие по меткам {r['label_agreement']:.0%}, "
              f"по атрибутам {r['attr_agreement']:.0%}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
