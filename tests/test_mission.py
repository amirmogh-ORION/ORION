import json
from datetime import datetime, timedelta, timezone
import pytest
from orion.mission import history, run_mission, parse_tenders, TENDERS, review_backlog, annual_facts
from orion.mission_sync import projection, sync_mission

NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def chart(latest=NOW, prices=None):
    prices = prices or [100+i for i in range(100)]
    times = [int((latest-timedelta(days=len(prices)-i-1)).timestamp()) for i in range(len(prices))]
    return json.dumps({"chart": {"error": None, "result": [{"meta": {"currency": "USD"}, "timestamp": times,
        "indicators": {"quote": [{"close": prices, "volume": [10000]*len(prices)}]}}]}})


def getter(url):
    if url == TENDERS:
        return "title,tender closing date,notice url,contracting organization\nUPS battery,2026-10-15,https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/x,NRC\n"
    return chart()


def test_freshness_gate_rejects_stale_and_future_data():
    for latest in (NOW-timedelta(days=10), NOW+timedelta(days=1)):
        assert history("X", "Stocks", NOW, lambda url: chart(latest))["status"] == "unavailable"


def test_infinite_prices_cannot_generate_features():
    result = history("X", "Stocks", NOW, lambda url: chart(prices=[float("inf")]*100))
    assert result["status"] == "unavailable"


def test_live_cycle_completes_traceable_decisions_without_inventing_qualification():
    report, state = run_mission({"Stocks": ["X"], "Crypto": ["Y"]}, [], now=NOW, getter=getter)
    assert report["metrics"]["instruments_observed"] == 2
    assert report["metrics"]["procurement_rows_observed"] == 1
    assert report["metrics"]["decisions"] == 3
    assert report["metrics"]["QUALIFIED"] == 0
    assert all(d["status"] == "NEEDS DATA" and d["missing"] and d["capital_action"] == "NO ACTION" for d in report["decisions"])
    assert len({t["id"] for t in report["tasks"]}) == len(report["tasks"])
    assert state["last_cycle"] == report["cycle_id"]


def test_failed_source_is_not_completed_task_or_observed_instrument():
    def fail(url):
        raise OSError("source offline")
    report, _ = run_mission({"Stocks": ["X"]}, [], now=NOW, getter=fail)
    assert report["metrics"]["instruments_observed"] == 0
    assert report["metrics"]["tasks_failed"] == 2
    assert not any(t["agent"] == "Data Acquisition Agent" and t["status"] == "COMPLETED" for t in report["tasks"])


def test_review_deadline_is_not_reset_and_historical_decisions_are_retained():
    backlog = [{"id": "a", "fields": {"Opportunity": "A", "Category": "Stocks", "Status": "DISCOVERY"}}]
    _, first = run_mission({}, backlog, now=NOW, getter=getter)
    report, second = run_mission({}, backlog, first, NOW+timedelta(days=2), getter)
    assert second["decisions"]["a"]["review_at"] == first["decisions"]["a"]["review_at"]
    assert report["metrics"]["overdue_reviews"] >= 1
    monitor = next(t for t in report["tasks"] if t["agent"] == "Monitoring Agent")
    assert "a" in monitor["output"]["overdue_ids"]
    _, third = run_mission({}, [], second, NOW+timedelta(days=3), getter)
    assert "a" in third["decisions"]


def test_existing_rejection_is_not_reopened():
    d = review_backlog({"id": "x", "fields": {"Opportunity": "X", "Status": "REJECTED"}}, NOW)
    assert d["status"] == "REJECTED"


def test_tender_schema_change_fails_closed():
    with pytest.raises(ValueError, match="schema changed"):
        parse_tenders("foo,bar\na,b", NOW)


def test_projection_has_provenance_and_preserves_original_evidence():
    backlog = [{"id": "a", "fields": {"Opportunity": "A", "Status": "DISCOVERY", "Evidence": "original claim"}}]
    report, _ = run_mission({"Stocks": ["X"]}, backlog, now=NOW, getter=getter)
    rows, grouped = projection(report, "https://github.com/owner/repo/actions/runs/1")
    assert rows["Research Sources"][1][0]["URL"].startswith("https://")
    assert "sha256" in rows["Research Sources"][1][0]["Key Finding"]
    old = next(r for r in rows["Opportunities"][1] if r["Opportunity"] == "A")
    assert "Evidence" not in old
    assert "Review due:" in old["Next Trigger"]


def test_follow_up_requires_new_observation_not_reused_stale_price():
    _, first = run_mission({"Stocks": ["X"]}, [], now=NOW, getter=getter)
    report, _ = run_mission({"Stocks": ["X"]}, [], first, NOW+timedelta(days=8),
                            lambda url: getter(url) if url == TENDERS else chart(NOW))
    assert report["metrics"]["outcomes_evaluated"] == 0


def test_filing_parser_rejects_future_filings_and_quarter_as_annual():
    def fact(start, end, filed, value):
        return {"form": "10-K", "start": start, "end": end, "filed": filed, "val": value}
    raw = json.dumps({"entityName": "Example", "facts": {"us-gaap": {"NetIncomeLoss": {"units": {"USD": [
        fact("2025-01-01","2025-12-31","2026-02-01",100),
        fact("2026-01-01","2026-12-31","2027-02-01",999),
        fact("2026-01-01","2026-03-31","2026-05-01",30)
    ]}}}}})
    result = annual_facts(raw, NOW)
    assert result["annual_facts"]["net_income"]["value"] == 100


def test_official_tender_without_notice_url_still_has_dataset_provenance():
    raw = ('title-titre-eng,tenderClosingDate-appelOffresDateCloture,noticeURL-URLavis-eng,'
           'solicitationNumber-numeroSollicitation\nUPS,2026-10-10,,ABC\n')
    _, candidates = parse_tenders(raw, NOW)
    assert candidates[0]["source"] == TENDERS
    assert candidates[0]["id"] == "tender:ABC"


def test_machine_triage_cannot_overwrite_external_analyst_decision():
    class Client:
        writes = []
        def records(self, table):
            if table == "Opportunities":
                return [{"fields": {"Opportunity": "A", "Status": "QUALIFIED",
                        "Actual Result": "Independent analyst qualification with evidence"}}]
            return []
        def upsert(self, table, key, records):
            self.writes.append((table, records))
    client = Client()
    backlog = [{"id": "a", "fields": {"Opportunity": "A", "Status": "DISCOVERY"}}]
    report, _ = run_mission({}, backlog, now=NOW, getter=getter)
    sync_mission(client, report, "https://github.com/owner/repo/actions/runs/1")
    assert not any(r.get("Opportunity") == "A" for table, rows in client.writes if table == "Opportunities" for r in rows)
