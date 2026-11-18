"""Tests for report_writer — empty-day proof-of-life behavior.

The scheduled execute→email pairs rely on a report file always existing for
the run date, even on days where no opportunity clears the edge threshold.
Without one, the paired email task finds no report and silently skips sending
(feedback_sameday_empty_emails). save_execution_report([]) must therefore write
a valid "0 orders" report rather than bailing out.
"""

from report_writer import save_execution_report, save_scan_report


class TestEmptyExecutionReport:
    def test_empty_orders_still_writes_file(self, tmp_path):
        """A no-opportunity day must still produce a proof-of-life report."""
        rpt = save_execution_report([], report_type="sports", output_dir=str(tmp_path))
        assert rpt is not None
        written = list(tmp_path.glob("*_sports_execution.md"))
        assert len(written) == 1

    def test_empty_report_content(self, tmp_path):
        """The empty report shows 0 orders and $0.00 total cost."""
        save_execution_report([], report_type="sports", output_dir=str(tmp_path))
        content = next(tmp_path.glob("*_sports_execution.md")).read_text(encoding="utf-8")
        assert "0 orders" in content
        assert "sized cost: $0.00" in content
        assert "## Orders" in content


class TestEmptyScanReport:
    def test_empty_scan_report_returns_none(self, tmp_path):
        """save_scan_report intentionally skips empty result sets — the
        execute-report path is what supplies the empty-day proof-of-life file."""
        rpt = save_scan_report([], report_type="sports", output_dir=str(tmp_path))
        assert rpt is None
        assert list(tmp_path.glob("*.md")) == []


class TestModeLine:
    """ER-12: the report says what happened, not what was requested."""

    def _orders(self, *outcomes):
        from kalshi_executor import SizedOrder
        from opportunity import Opportunity

        out = []
        for i, o in enumerate(outcomes):
            opp = Opportunity(
                ticker=f"KXNBAGAME-26APR04T{i}-A",
                title="g",
                category="game",
                side="yes",
                market_price=0.5,
                fair_value=0.6,
                edge=0.1,
                edge_source="t",
                confidence="high",
                liquidity_score=1.0,
                composite_score=1.0,
                details={},
            )
            out.append(SizedOrder(opp, 2, 50, 1.0, 0.01, "APPROVED", outcome=o))
        return out

    def _write(self, tmp_path, orders, mode):
        save_execution_report(orders, output_dir=str(tmp_path), mode=mode)
        return next(tmp_path.glob("*_execution.md")).read_text(encoding="utf-8")

    def test_blocked_live_run_says_zero_placed(self, tmp_path):
        text = self._write(tmp_path, self._orders("blocked", "blocked"), "LIVE · REAL MONEY · PROD")
        assert "**LIVE · REAL MONEY · PROD** · 0 placed · 2 blocked" in text
        assert "**Placed cost: $0.00**" in text

    def test_mixed_live_run_counts_each_outcome(self, tmp_path):
        text = self._write(
            tmp_path, self._orders("placed", "failed", "not attempted"), "LIVE · REAL MONEY · PROD"
        )
        assert "1 placed · 1 failed · 1 not attempted" in text
        assert "**Placed cost: $1.00**" in text and "| not attempted |" in text

    def test_dry_run_never_claims_placed(self, tmp_path):
        text = self._write(tmp_path, self._orders("dry_run"), "DRY RUN · nothing sent")
        assert "**DRY RUN · nothing sent** · 1 dry run" in text and "placed" not in text
