import sys

import pandas as pd


def kappa(a, b):
    labels = sorted(set(a) | set(b))
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a == l).mean() * (b == l).mean() for l in labels)
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0


def compare(path_a, path_b):
    A = pd.read_csv(path_a, sep="\t")
    B = pd.read_csv(path_b, sep="\t")
    m = A.merge(B, on=["doc", "sent", "idx", "token"], suffixes=("_a", "_b"))
    po, k = kappa(m["ner_a"], m["ner_b"])
    diff = m[m["ner_a"] != m["ner_b"]][["doc", "sent", "token", "ner_a", "ner_b"]]
    return po, k, diff


if __name__ == "__main__":
    po, k, diff = compare(sys.argv[1], sys.argv[2])
    print(f"совпадение меток: {po:.1%}, kappa = {k:.3f}, расхождений: {len(diff)}")
    print(diff.head(30).to_string(index=False))
