"""ER-52: the order preview fits a 100-column log, one line per order."""

import io

from rich.console import Console

from kalshi_executor import SizedOrder, preview_table
from opportunity import Opportunity

ROWS = [
    ("KXMLBGAME-26AUG271905NYYBOS-NYY", "New York Y vs Boston Winner?", "game", "yes"),
    (
        "KXNFLSPREAD-26SEP13MIALV-MIA7",
        "Miami wins by over 7.5 points in the Miami at Las Vegas professional football game",
        "spread",
        "no",
    ),
    ("KXNBATOTAL-26APR04LALBOS-247", "Lakers at Celtics: Total Points", "total", "yes"),
    (
        "KXSB-26-KC",
        "Will the Kansas City Chiefs win the Pro Football Championship this season?",
        "futures",
        "yes",
    ),
]


def _order(ticker, title, category, side):
    opp = Opportunity(
        ticker=ticker,
        title=title,
        category=category,
        side=side,
        market_price=0.45,
        fair_value=0.55,
        edge=0.1,
        edge_source="test",
        confidence="high",
        liquidity_score=8.0,
        composite_score=8.5,
        details={},
    )
    return SizedOrder(
        opportunity=opp,
        contracts=12,
        price_cents=45,
        cost_dollars=5.4,
        bankroll_pct=0.05,
        risk_approval="APPROVED",
    )


def test_preview_fits_100_columns_one_line_per_order():
    buf = io.StringIO()
    console = Console(file=buf, width=100, color_system=None, legacy_windows=False)
    console.print(preview_table([_order(*r) for r in ROWS], "PREVIEW"))
    lines = buf.getvalue().splitlines()
    assert max(len(line) for line in lines) <= 100
    for i in range(1, len(ROWS) + 1):
        assert sum(1 for line in lines if line.lstrip().startswith(f"{i} ")) == 1
    body = [line for line in lines if line.strip() and line.lstrip()[0].isdigit()]
    assert len(body) == len(ROWS)
    assert "ML NY Yankees" in body[0] and "+10.0%" in body[0]
