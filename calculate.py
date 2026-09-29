"""Контрольный пересчёт исследования: баллы из SCORE_MATRIX.csv × веса SCORING_MODEL.csv.

    python calculate.py                 # пересчитать баллы и места
    python calculate.py --sensitivity   # повторить анализ устойчивости (сид в RESULTS.json)
"""
import csv, json, random, sys
from pathlib import Path

ROOT = Path(__file__).parent
weights = {r["metric_id"]: float(r["weight"]) for r in csv.DictReader(open(ROOT / "SCORING_MODEL.csv", encoding="utf-8"))}
rows = list(csv.DictReader(open(ROOT / "SCORE_MATRIX.csv", encoding="utf-8")))
order = list(weights)


def score(r, w):
    return round(sum(float(r[m] or 0) / 5 * w[m] for m in w), 6)


for r in rows:
    calc, declared = score(r, weights), float(r["final_score"])
    if abs(calc - declared) > 1e-6:
        sys.exit(f"Расхождение: {r['participant']}: расчёт {calc}, в матрице {declared}")
    mark = "" if r["eligible"] == "TRUE" else "  [вне допуска]"
    print(f"{r['rank'] or '--':>2}. {r['participant']}: {calc:g}/100{mark}")
print("OK: сумма весов =", sum(weights.values()), "· участников =", len(rows))

if "--sensitivity" in sys.argv:
    cfg = json.load(open(ROOT / "RESULTS.json", encoding="utf-8"))["sensitivity"]
    rnd = random.Random(cfg["seed"])
    elig = [r for r in rows if r["eligible"] == "TRUE"]
    dist = {r["participant"]: {} for r in elig}
    for _ in range(cfg["runs"]):
        w = {k: v * rnd.uniform(1 - cfg["spread"], 1 + cfg["spread"]) for k, v in weights.items()}
        n = 100 / sum(w.values())
        w = {k: v * n for k, v in w.items()}
        ranked = sorted(elig, key=lambda r: (-score(r, w), [-float(r[m] or 0) for m in order]))
        for i, r in enumerate(ranked, 1):
            dist[r["participant"]][i] = dist[r["participant"]].get(i, 0) + 1
    for name, d in dist.items():
        print(name, "→", ", ".join(f"{k}-е место: {v}" for k, v in sorted(d.items())))
