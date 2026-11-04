import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATTRIBUTES = {
    "sex": (["male", "female", "unknown"], "unknown"),
    "age": (["adult", "juvenile", "unknown"], "unknown"),
    "pose": (["perched", "flying", "swimming", "standing", "unknown"], "unknown"),
    "plumage_main": (["gray", "brown", "black", "white", "black_white", "multicolor", "unknown"], "unknown"),
}
MIN_BOX = 32
PALETTE = ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#46f0f0", "#f032e6", "#bcf60c",
           "#008080"]


def load_species():
    with open(os.path.join(ROOT, "metadata", "species.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cvat_labels():
    labels = []
    for i, sp in enumerate(load_species()):
        labels.append({"name": sp["slug"], "color": PALETTE[i % len(PALETTE)], "type": "rectangle",
                       "attributes": [{"name": n, "input_type": "select", "mutable": False, "default_value": d,
                                       "values": v} for n, (v, d) in ATTRIBUTES.items()]})
    return labels
