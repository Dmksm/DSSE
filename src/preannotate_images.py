import argparse
import json
import os
from xml.etree import ElementTree as ET

from PIL import Image

from image_schema import ATTRIBUTES, ROOT, cvat_labels, load_species

IMG_DIR = os.path.join(ROOT, "data", "images")
OUT = os.path.join(ROOT, "annotations", "images")
EXTS = {".jpg", ".jpeg", ".png"}
COCO_BIRD_CLASS = 14

_model = None


def detect_birds(path, conf=0.25):
    global _model
    if _model is None:
        from ultralytics import YOLO
        _model = YOLO("yolov8n.pt")
    res = _model.predict(path, conf=conf, classes=[COCO_BIRD_CLASS], verbose=False)[0]
    return [(*map(float, b.xyxy[0].tolist()), float(b.conf[0])) for b in res.boxes]


def list_images():
    items = []
    for sp in load_species():
        d = os.path.join(IMG_DIR, sp["slug"])
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if os.path.splitext(fn)[1].lower() in EXTS:
                    items.append((sp["slug"], f"{sp['slug']}/{fn}", os.path.join(d, fn)))
    return items


def write_labels(parent):
    labels = ET.SubElement(parent, "labels")
    for lb in cvat_labels():
        el = ET.SubElement(labels, "label")
        ET.SubElement(el, "name").text = lb["name"]
        ET.SubElement(el, "color").text = lb["color"]
        ET.SubElement(el, "type").text = "rectangle"
        attrs = ET.SubElement(el, "attributes")
        for a in lb["attributes"]:
            at = ET.SubElement(attrs, "attribute")
            ET.SubElement(at, "name").text = a["name"]
            ET.SubElement(at, "mutable").text = "False"
            ET.SubElement(at, "input_type").text = "select"
            ET.SubElement(at, "default_value").text = a["default_value"]
            ET.SubElement(at, "values").text = "\n".join(a["values"])


def build(conf=0.25, detector=detect_birds):
    os.makedirs(OUT, exist_ok=True)
    species = load_species()
    root = ET.Element("annotations")
    ET.SubElement(root, "version").text = "1.1"
    task = ET.SubElement(ET.SubElement(root, "meta"), "task")
    ET.SubElement(task, "name").text = "birds_detection"
    write_labels(task)
    coco = {"images": [], "annotations": [],
            "categories": [{"id": i + 1, "name": s["slug"]} for i, s in enumerate(species)]}
    cat_id = {s["slug"]: i + 1 for i, s in enumerate(species)}
    manual, ann_id = [], 1
    for img_id, (slug, rel, path) in enumerate(list_images()):
        with Image.open(path) as im:
            w, h = im.size
        el = ET.SubElement(root, "image", id=str(img_id), name=rel, width=str(w), height=str(h))
        coco["images"].append({"id": img_id, "file_name": rel, "width": w, "height": h})
        boxes = detector(path, conf)
        if not boxes:
            manual.append(rel)
        for x1, y1, x2, y2, score in boxes:
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
            box = ET.SubElement(el, "box", label=slug, source="auto", occluded="0", xtl=f"{x1:.2f}",
                                ytl=f"{y1:.2f}", xbr=f"{x2:.2f}", ybr=f"{y2:.2f}", z_order="0")
            for name, (_, default) in ATTRIBUTES.items():
                ET.SubElement(box, "attribute", name=name).text = default
            coco["annotations"].append({"id": ann_id, "image_id": img_id, "category_id": cat_id[slug], "iscrowd": 0,
                                        "bbox": [round(x1, 2), round(y1, 2), round(x2 - x1, 2), round(y2 - y1, 2)],
                                        "area": round((x2 - x1) * (y2 - y1), 2), "score": round(score, 3),
                                        "attributes": {n: d for n, (_, d) in ATTRIBUTES.items()}})
            ann_id += 1
    ET.indent(root)
    ET.ElementTree(root).write(os.path.join(OUT, "cvat_preannotation.xml"), encoding="utf-8", xml_declaration=True)
    with open(os.path.join(OUT, "preannotation_coco.json"), "w", encoding="utf-8") as f:
        json.dump(coco, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "cvat_labels.json"), "w", encoding="utf-8") as f:
        json.dump(cvat_labels(), f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "needs_manual.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(manual))
    print(f"изображений: {len(coco['images'])}, рамок: {len(coco['annotations'])}, без детекции: {len(manual)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--conf", type=float, default=0.25)
    build(ap.parse_args().conf)
