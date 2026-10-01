"""Idempotent Airtable projection of attributable deterministic mission tasks."""
import json
import os
from pathlib import Path
import time
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class Airtable:
    def __init__(self, base, token):
        if not base or not token:
            raise ValueError("Airtable base/token required")
        self.base, self.token = base, token

    def request(self, table, method="GET", body=None, query=None):
        url = f"https://api.airtable.com/v0/{quote(self.base)}/{quote(table)}"
        if query:
            url += "?" + urlencode(query)
        req = Request(url, method=method,
                      headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
                      data=json.dumps(body).encode() if body is not None else None)
        # Stay below Airtable's per-base request rate; no secrets are logged.
        time.sleep(.22)
        with urlopen(req, timeout=20) as response:
            return json.load(response)

    def records(self, table):
        records, offset = [], None
        while True:
            query = {"pageSize": 100}
            if offset:
                query["offset"] = offset
            data = self.request(table, query=query)
            records.extend(data["records"])
            offset = data.get("offset")
            if not offset:
                return records

    def upsert(self, table, key, records):
        for start in range(0, len(records), 10):
            self.request(table, "PATCH", {"performUpsert": {"fieldsToMergeOn": [key]},
                         "typecast": True, "records": [{"fields": r} for r in records[start:start+10]]})


def pull_backlog(client, path):
    records = client.records("Opportunities")
    # Only original/manual opportunities; program-generated candidates have a prefix.
    records = [r for r in records if not r["fields"].get("Opportunity", "").startswith("ORION lead:")]
    data = [{"id": r["id"], "created_at": r.get("createdTime"), "fields": r["fields"]} for r in records]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2))
    return len(data)


def projection(report, run_url):
    cycle, time_at = report["cycle_id"], report["completed_at"]
    rows = {}
    rows["Runs"] = ("Run", [{"Run": "Mission "+cycle, "Run Type": "FULL SCAN",
        "Status": "FAILED" if report["metrics"]["tasks_failed"] else "COMPLETED",
        "Started": report["started_at"], "Completed": time_at,
        "Output Summary": json.dumps(report["metrics"])+"; Evidence: "+run_url+"; Deterministic workers; no live trades."}])
    grouped = {}
    for t in report["tasks"]:
        grouped.setdefault(t["agent"], []).append(t)
    activities = []
    for agent, tasks in grouped.items():
        failed = sum(t["status"] != "COMPLETED" for t in tasks)
        activities.append({"Event": cycle+":"+agent, "Agent": agent,
            "Event Type": "ERROR" if failed else "RESEARCH",
            "Timestamp": time_at, "Details": json.dumps({"assigned": len(tasks), "failed": failed,
            "mode": report["mode"], "outputs": tasks[:3], "complete_outputs": run_url})})
    rows["Activity Log"] = ("Event", activities)
    sources = [{"Source": "ORION history: "+o["symbol"], "URL": o["source"],
                "Source Type": "Market Data", "Checked": o["observed_at"],
                "Key Finding": json.dumps({"bar": o["latest_bar"], "sha256": o["source_sha256"],
                    "features": o["features"], "limitation": "Single provider, descriptive observations", "run": run_url})}
               for o in report["observations"] if o["status"] == "observed"]
    p = report["procurement"]
    for f in report.get("fundamentals", []):
        if f["status"] == "observed":
            sources.append({"Source": "ORION SEC financial facts: "+f["symbol"], "URL": f["source"],
                "Source Type": "Filing", "Checked": f["observed_at"],
                "Key Finding": json.dumps({"annual_facts": f["annual_facts"], "sha256": f["source_sha256"], "run": run_url})})
    if p["status"] == "observed":
        sources.append({"Source": "ORION CanadaBuys open tenders", "URL": p["source"],
                        "Source Type": "Government", "Checked": p["observed_at"],
                        "Key Finding": json.dumps({"rows": p["rows_observed"], "sha256": p["source_sha256"], "run": run_url})})
    rows["Research Sources"] = ("Source", sources)
    decisions = []
    for d in report["decisions"]:
        name = d["name"] if d["origin"] == "airtable_backlog" else "ORION lead: "+d["name"]
        decisions.append({"Opportunity": name, "Category": d["category"], "Status": d["status"],
                          "Last Updated": d["evaluated_at"],
                          "Actual Result": "Research decision: "+d["status"]+" — "+d["reason"],
                          "Next Trigger": f"Owner: {d['owner']}; Review due: {d['review_at']}; Missing: "+", ".join(d["missing"])+
                                          "; Capital: NO ACTION; Audit: "+run_url})
        if d["origin"] != "airtable_backlog":
            decisions[-1]["Evidence"] = json.dumps({"source": d.get("source"), "sha256": d.get("source_sha256"),
                "features": d.get("features"), "cycle": cycle, "mode": report["mode"], "run": run_url})
    rows["Opportunities"] = ("Opportunity", decisions)
    return rows, grouped


def sync_mission(client, report, run_url):
    rows, grouped = projection(report, run_url)
    for table, (key, records) in rows.items():
        if records:
            client.upsert(table, key, records)
    agents = {r["fields"].get("Agent"): r for r in client.records("Agents")}
    updates = []
    for name, tasks in grouped.items():
        if name not in agents:
            continue
        good = [t for t in tasks if t["status"] == "COMPLETED"]
        fields = {"Current Task": f"Last cycle: {len(good)}/{len(tasks)} tasks completed. Deterministic worker. Evidence: {run_url}",
                  "Heartbeat": report["completed_at"], "Version": report["version"],
                  "Status": "WAITING" if good else "ERROR"}
        if good:
            fields["Last Completed"] = report["completed_at"]
        updates.append({"id": agents[name]["id"], "fields": fields})
    for start in range(0, len(updates), 10):
        client.request("Agents", "PATCH", {"records": updates[start:start+10]})


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pull", action="store_true")
    args = parser.parse_args()
    client = Airtable(os.getenv("ORION_AIRTABLE_BASE_ID"), os.getenv("ORION_AIRTABLE_TOKEN"))
    if args.pull:
        print(f"Loaded {pull_backlog(client, 'state/backlog.json')} current opportunities")
    else:
        report = json.loads(Path("reports/mission.json").read_text())
        url = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
        sync_mission(client, report, url)
        print("Mission decisions, source evidence and task outputs synchronized")


if __name__ == "__main__":
    main()
