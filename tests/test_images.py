import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from PIL import Image

import image_schema
import preannotate_images as pre
import validate_image_annotations as val


def run():
    tmp = tempfile.mkdtemp()
    for d in ("metadata", "data/images", "annotations/images"):
        os.makedirs(os.path.join(tmp, d))
    shutil.copy(os.path.join(ROOT, "metadata", "species.csv"), os.path.join(tmp, "metadata"))
    for slug in ("great_tit", "mallard"):
        os.makedirs(os.path.join(tmp, "data/images", slug))
        for i in range(1, 4):
            Image.new("RGB", (400, 300), "gray").save(os.path.join(tmp, f"data/images/{slug}/{slug}_{i:02d}.jpg"))
    for m in (image_schema, pre, val):
        m.ROOT = tmp
    pre.IMG_DIR, pre.OUT = os.path.join(tmp, "data/images"), os.path.join(tmp, "annotations/images")
    fake = lambda path, conf: [] if path.endswith("mallard_03.jpg") else [(50, 40, 250, 200, 0.9)]
    pre.build(detector=fake)
    xml = os.path.join(pre.OUT, "cvat_preannotation.xml")
    _, problems = val.validate(xml)
    assert problems == ["mallard/mallard_03.jpg: нет рамок"], problems
    with open(xml, encoding="utf-8") as f:
        txt = f.read()
    txt = txt.replace('xbr="250.00"', 'xbr="500.00"', 1).replace('<attribute name="sex">unknown<',
                                                                '<attribute name="sex">purple<', 1)
    bad = os.path.join(pre.OUT, "bad.xml")
    with open(bad, "w", encoding="utf-8") as f:
        f.write(txt)
    _, problems2 = val.validate(bad)
    assert any("за границы" in p for p in problems2) and any("недопустимый атрибут" in p for p in problems2), problems2
    r = val.compare(xml, xml)
    assert r["mean_iou"] > 0.99 and r["label_agreement"] == 1.0, r
    print("тесты пройдены")
    shutil.rmtree(tmp)


if __name__ == "__main__":
    run()
