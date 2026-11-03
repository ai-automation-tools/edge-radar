"""Fit and validate the key-number NFL margin model (edge_detector._NFL_KEY_WEIGHTS).

NFL final margins pile on 3 and 7; a normal CDF spreads that mass evenly, so it
over-prices "a small favourite wins by over 7.5" by ~8pts (2026-11-03). The
production model weights the normal mass at each whole-number margin k by
w[|k|], fitted here as observed/expected counts against a normal centred on the
closing line, shrunk toward 1.0 by a pseudo-count.

    python scripts/backtest/fit_nfl_margin.py            # holdout table + refit
    python scripts/backtest/fit_nfl_margin.py --csv PATH

Data: nflverse games.csv (closing spread, spread odds, final score). Validation
fits on <= TRAIN_LAST and scores later seasons with the PRODUCTION functions,
so a holdout win is a win for the code that runs. The printed weights are fitted
on every season; paste them into edge_detector._NFL_KEY_WEIGHTS by hand.
Read-only: it never edits code or .env.
"""

from __future__ import annotations

import argparse
import csv
import sys
import urllib.request
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts" / "kalshi"), str(ROOT / "scripts" / "shared")]

from edge_detector import (  # noqa: E402
    _MARGIN_K,
    discrete_cover_prob,
    discrete_infer_mean,
)

URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
CACHE = ROOT / "data" / "cache" / "nflverse_games.csv"
FIRST_SEASON = 2012
TRAIN_LAST = 2020
N_WEIGHTS = 31  # |k| 0..30; beyond that the weight is 1.0
PSEUDO = 20.0
SD_GRID = (11.0, 11.5, 12.0, 12.5, 13.0)
STRIKES = (1.5, 3.5, 4.5, 7.5, 10.5, 14.5, 17.5, 21.5)


def _implied(american: float) -> float:
    return 100 / (american + 100) if american > 0 else -american / (-american + 100)


def load(path: Path) -> list[tuple[int, float, float, float]]:
    """(season, fav line, fav margin, devigged P(fav covers)) per game."""
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not (r["result"] and r["spread_line"] and r["home_spread_odds"]):
                continue
            if int(r["season"]) < FIRST_SEASON:
                continue
            line, margin = float(r["spread_line"]), float(r["result"])
            ph, pa = _implied(float(r["home_spread_odds"])), _implied(float(r["away_spread_odds"]))
            p = ph / (ph + pa)
            if line < 0:
                line, margin, p = -line, -margin, 1 - p
            out.append((int(r["season"]), line, margin, p))
    return out


def fit_weights(games, sd: float) -> tuple[float, ...]:
    obs = np.zeros(N_WEIGHTS)
    exp = np.zeros(N_WEIGHTS)
    a = np.abs(_MARGIN_K)
    keep = a < N_WEIGHTS
    for _, line, margin, _ in games:
        mass = norm.cdf((_MARGIN_K + 0.5 - line) / sd) - norm.cdf((_MARGIN_K - 0.5 - line) / sd)
        np.add.at(exp, a[keep], mass[keep])
        if abs(margin) < N_WEIGHTS:
            obs[int(abs(margin))] += 1
    return tuple(float(x) for x in np.round((obs + PSEUDO) / (exp + PSEUDO), 3))


def means(games, sd, weights) -> list[float]:
    """Each game's mean margin, inferred from its own closing quote (once per game)."""
    return [discrete_infer_mean(sd, line, p, weights) for _, line, _, p in games]


def predict(mus, sd, weights, strike):
    return [discrete_cover_prob(mu, sd, strike, weights) for mu in mus]


def brier(ps, games, strike) -> float:
    return float(np.mean([(p - (m > strike)) ** 2 for p, (_, _, m, _) in zip(ps, games)]))


def choose_sd(games):
    best = None
    for sd in SD_GRID:
        w = fit_weights(games, sd)
        mus = means(games, sd, w)
        b = np.mean([brier(predict(mus, sd, w, s), games, s) for s in STRIKES])
        print(f"  sd {sd:4.1f}: Brier {b:.5f}")
        if best is None or b < best[0]:
            best = (b, sd, w)
    return best[1], best[2]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", type=Path, default=CACHE)
    a = ap.parse_args()
    if not a.csv.exists():
        a.csv.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL, a.csv)
    games = load(a.csv)
    train = [g for g in games if g[0] <= TRAIN_LAST]
    test = [g for g in games if g[0] > TRAIN_LAST]
    print(f"{len(games)} games ({len(train)} train <= {TRAIN_LAST}, {len(test)} holdout)\n")

    print("Train fit:")
    sd, w = choose_sd(train)
    print(f"\nHOLDOUT (fitted on <= {TRAIN_LAST}, sd {sd}) vs normal(13.5) as the code used")
    print("strike  fav line   n   actual   normal (Brier)    discrete (Brier)")
    bands = {}
    for lo, hi in ((0.5, 4.0), (4.5, 7.5), (8.0, 30.0)):
        g = [x for x in test if lo <= x[1] <= hi]
        if len(g) >= 50:
            bands[(lo, hi)] = (g, means(g, sd, w))
    for s in STRIKES:
        for (lo, hi), (g, mus) in bands.items():
            pn = [1 - norm.cdf(s, line - 13.5 * norm.ppf(1 - p), 13.5) for _, line, _, p in g]
            pd = predict(mus, sd, w, s)
            act = np.mean([m > s for _, _, m, _ in g])
            print(
                f">{s:<5} {lo:4}-{hi:<4} {len(g):5}  {act:6.1%}   "
                f"{np.mean(pn):6.1%} ({brier(pn, g, s):.4f})   "
                f"{np.mean(pd):6.1%} ({brier(pd, g, s):.4f})"
            )

    print("\nAll-season refit (production values):")
    sd_all, w_all = choose_sd(games)
    print(f"\n_NFL_DISCRETE_SD = {sd_all}")
    print("_NFL_KEY_WEIGHTS = (")
    for i in range(0, N_WEIGHTS, 10):
        chunk = w_all[i : i + 10]
        print("    " + ", ".join(f"{x:.3f}" for x in chunk) + f",  # {i}-{i + len(chunk) - 1}")
    print(")")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
