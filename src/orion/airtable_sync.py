"""Write one verified GitHub price-snapshot run to Airtable; no research claims."""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


def expected_us_session(observed_at):
    return acceptable_us_sessions(observed_at)[0]


def acceptable_us_sessions(observed_at):
    local = datetime.fromisoformat(observed_at.replace('Z', '+00:00')).astimezone(ZoneInfo('America/New_York'))
    day = local.date()
    previous = day - timedelta(days=1)
    while previous.weekday() >= 5:
        previous -= timedelta(days=1)
    if local.weekday() >= 5:
        return (previous.isoformat(),)
    minutes = local.hour * 60 + local.minute
    if minutes < 9 * 60 + 30:
        return (previous.isoformat(),)
    if minutes < 16 * 60:
        # Yahoo's daily bar can be either today's live observation or the
        # previous close shortly after the opening bell. Both are valid price
        # observations, but neither is treated as a completed research signal.
        return (day.isoformat(), previous.isoformat())
    return (day.isoformat(),)


def record_payloads(report, run_id, repository):
    if report.get("kind") != "price_observation_only":
        raise ValueError("Unexpected report kind")
    results = report.get("results", [])
    observed = [item for item in results if item.get("status") == "observed"]
    failed = [item for item in results if item.get("status") != "observed"]
    acceptable = acceptable_us_sessions(report["observed_at"])
    stale = [item for item in observed if item.get("date") not in acceptable]
    good = bool(observed) and not stale and not failed
    status = "COMPLETED" if good else "FAILED"
    run_url = f"https://github.com/{repository}/actions/runs/{run_id}"
    label = f"GitHub market snapshot {run_id}"
    summary = (
        f"{len(observed)} observed prices: "
        + ", ".join(f"{item['symbol']} ({item['date']})" for item in observed)
        + f"; {len(failed)} unavailable/invalid; {len(stale)} stale/outside accepted US session dates "
        + f"{', '.join(acceptable)}. "
        + f"Source artifact: {run_url}. "
        "Price observations only; no research conclusions, signals, or trades."
    )
    started = report["observed_at"]
    return [
        ("Runs", "Run", label, {
            "Run": label, "Run Type": "MARKETS", "Status": status,
            "Started": started, "Completed": started, "Output Summary": summary,
        }),
        ("Activity Log", "Event", label, {
            "Event": label, "Agent": "GitHub Actions market snapshot job",
            "Event Type": "SCAN" if good else "ERROR", "Details": summary, "Timestamp": started,
        }),
    ]


def sync(report, run_id, repository, base_id, token, opener=urlopen):
    if not base_id or not token:
        raise ValueError("ORION_AIRTABLE_BASE_ID and ORION_AIRTABLE_TOKEN are required")
    if not run_id.isdigit() or repository != "amirmogh-ORION/ORION":
        raise ValueError("Invalid GitHub run identity")
    for table, key, label, fields in record_payloads(report, run_id, repository):
        endpoint = f"https://api.airtable.com/v0/{quote(base_id)}/{quote(table)}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        query = urlencode({"filterByFormula": f"{{{key}}}='{label}'", "maxRecords": 1})
        with opener(Request(endpoint + "?" + query, headers=headers), timeout=15) as response:
            existing = json.load(response).get("records", [])
        if existing:
            continue
        body = json.dumps({"records": [{"fields": fields}]}).encode()
        with opener(Request(endpoint, data=body, headers=headers, method="POST"), timeout=15) as response:
            created = json.load(response).get("records", [])
        if len(created) != 1:
            raise ValueError(f"Failed to create {table} record")


def main():
    report = json.loads(Path("reports/latest.json").read_text(encoding="utf-8"))
    sync(report, os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_REPOSITORY"],
         os.environ.get("ORION_AIRTABLE_BASE_ID"), os.environ.get("ORION_AIRTABLE_TOKEN"))
    print("Airtable run and activity records synchronized")
    if record_payloads(report, os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_REPOSITORY"])[0][3]["Status"] != "COMPLETED":
        raise SystemExit("Market snapshot failed data quality gate")


if __name__ == "__main__":
    main()
