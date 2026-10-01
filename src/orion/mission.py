"""Scheduled evidence-gated research workers. No LLM, live trades or invented theses.

Workers perform distinct, inspectable computations, not simulated human agents.
Technical screening produces research leads, never a valuation or BUY signal.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import statistics
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
TENDERS = "https://canadabuys.canada.ca/opendata/pub/openTenderNotice-ouvertAvisAppelOffres.csv?orion=1"
VERSION = "mission-v1"


def iso(value):
    return value.astimezone(timezone.utc).isoformat()


def fetch(url):
    # Only known public data hosts; never follow user-supplied arbitrary URLs.
    if urlparse(url).hostname not in {"query1.finance.yahoo.com", "canadabuys.canada.ca", "www.sec.gov", "data.sec.gov"}:
        raise ValueError("Unapproved data host")
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as response:
        data = response.read(30_000_001)
    if len(data) > 30_000_000:
        raise ValueError("Source exceeds size limit")
    return data.decode("utf-8-sig")


def history(symbol, category, now, getter=fetch):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol)}?range=1y&interval=1d"
    try:
        raw = getter(url)
        chart = json.loads(raw)["chart"]
        if chart.get("error"):
            raise ValueError(str(chart["error"]))
        series = chart["result"][0]
        bars = series["indicators"]["quote"][0]
        points = []
        for i, timestamp in enumerate(series.get("timestamp", [])):
            close = bars["close"][i]
            volume = (bars.get("volume") or [None] * len(bars["close"]))[i]
            if close is not None and math.isfinite(close) and close > 0:
                points.append({"time": timestamp, "close": close, "volume": volume})
        if len(points) < 61:
            raise ValueError("Fewer than 61 usable observations")
        if any(a["time"] >= b["time"] for a, b in zip(points, points[1:])):
            raise ValueError("Non-monotonic observations")
        latest = datetime.fromtimestamp(points[-1]["time"], timezone.utc)
        # Conservative wall-clock age supports weekends/holidays without claiming
        # an exchange-calendar check. Old/future data never advances screening.
        if latest > now + timedelta(minutes=5) or now - latest > timedelta(days=5):
            raise ValueError("Stale or future-dated observations")
        closes = [p["close"] for p in points]
        returns = [b/a - 1 for a, b in zip(closes, closes[1:])]
        peak, drawdown = closes[0], 0.0
        for close in closes:
            peak = max(peak, close)
            drawdown = min(drawdown, close/peak - 1)
        volumes = [p["volume"] for p in points[-21:-1] if p["volume"] is not None and p["volume"] > 0]
        avg_volume = statistics.mean(volumes) if volumes else None
        volume_ratio = points[-1]["volume"] / avg_volume if avg_volume and points[-1]["volume"] is not None else None
        features = {
            "last": closes[-1], "return_20d": closes[-1]/closes[-21]-1,
            "return_60d": closes[-1]/closes[-61]-1,
            "volatility_annualized": statistics.stdev(returns[-60:])*math.sqrt(365 if category == "Crypto" else 252),
            "max_drawdown_observed": drawdown,
            "volume_ratio": volume_ratio, "avg_daily_notional": avg_volume*closes[-1] if avg_volume else None,
            "bars": len(points),
        }
        return {"symbol": symbol, "category": category, "status": "observed",
                "source": url, "source_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "observed_at": iso(now), "latest_bar": iso(latest), "currency": series.get("meta", {}).get("currency"),
                "features": features, "points": points}
    except (OSError, ValueError, KeyError, IndexError, TypeError, statistics.StatisticsError) as exc:
        return {"symbol": symbol, "category": category, "status": "unavailable", "source": url, "error": str(exc)}


def parse_tenders(raw, now):
    reader = csv.DictReader(io.StringIO(raw))
    headers = reader.fieldnames or []
    def column(*names):
        for name in names:
            for header in headers:
                if name == header.lower().strip():
                    return header
        return None
    title = column("title", "title-titre-eng", "title-eng", "title-titre")
    closing = column("tender closing date", "tenderclosingdate-appeloffresdatecloture", "tenderclosingdate-datecloture", "tender-closing-date", "tender closing date-date de clôture")
    link = column("notice url", "noticeurl-urlavis-eng", "noticeurl-urlavis", "url")
    buyer = column("contracting organization", "contractingentityname-nomentitcontractante-eng", "contractingentity-entitecontractante-eng", "contracting-entity")
    ident = column("solicitation number", "solicitationnumber-numerosollicitation", "reference number")
    if not all((title, closing, link)):
        raise ValueError("CanadaBuys schema changed; required title/closing/URL columns missing: " + ", ".join(headers))
    results, total = [], 0
    keywords = ("cable", "power", "electrical", "battery", "ups", "uninterruptible", "cooling", "medical",
                "dental", "hardware", "computer", "consumable", "network", "server", "switch", "pump")
    for row in reader:
        total += 1
        name = row.get(title, "")
        if not any(word in name.lower() for word in keywords):
            continue
        try:
            date = datetime.fromisoformat(row[closing].replace("Z", "+00:00"))
            if date.tzinfo is None:
                # Preserve the supplied date; exact local deadline needs notice verification.
                date = date.replace(tzinfo=timezone.utc)
        except (ValueError, KeyError):
            continue
        days = (date.date() - now.date()).days
        if days < 0:
            continue
        results.append({"id": "tender:" + (row.get(ident) or row[link]), "name": name,
                        "category": "Procurement", "source": row[link],
                        "buyer": row.get(buyer, "") if buyer else "", "closing_date": iso(date),
                        "days_remaining": days, "source_observed_at": iso(now)})
    return total, sorted(results, key=lambda r: (r["days_remaining"], r["id"]))


def tender_scan(now, getter=fetch):
    try:
        raw = getter(TENDERS)
        total, candidates = parse_tenders(raw, now)
        return {"status": "observed", "source": TENDERS, "source_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "rows_observed": total, "candidates": candidates, "observed_at": iso(now)}
    except (OSError, ValueError, csv.Error) as exc:
        return {"status": "unavailable", "source": TENDERS, "error": str(exc), "rows_observed": 0, "candidates": []}


def task(tasks, cycle, agent, subject, output, now, status="COMPLETED"):
    tasks.append({"id": f"{cycle}:{len(tasks)+1}", "agent": agent, "subject": subject,
                  "status": status, "completed_at": iso(now), "output": output, "version": VERSION})


def review_backlog(record, now):
    fields = record["fields"]
    category = fields.get("Category", "Other")
    missing = ["fresh source-linked thesis", "verified economics", "capital requirement",
               "downside estimate", "entry and exit conditions", "risk review"]
    if category in {"Business", "Procurement"}:
        missing = ["exact buyer RFQ/specification and deadline", "compliant supplier quote",
                   "landed cost including freight, tax, FX and warranty", "buyer price and payment terms",
                   "supplier eligibility", "working-capital and execution risk"]
    # Existing confidence/price targets were not accompanied by source-normalized
    # verification. Preserve them in input history, never promote them as facts.
    rejected = fields.get("Status") == "REJECTED"
    return {"id": record["id"], "name": fields["Opportunity"], "category": category,
            "status": "REJECTED" if rejected else "NEEDS DATA", "origin": "airtable_backlog",
            "reason": "Existing rejection retained; conflicting deadline requires re-verification." if rejected else
                      "Prior narrative/targets do not establish an evidence-backed economic decision.",
            "missing": [] if rejected else missing, "owner": "Due Diligence Agent" if category in {"Procurement", "IPOs"} else "Research Agent",
            "next_action": "Fetch the exact official notice/filing and obtain missing inputs before qualification.",
            "review_at": iso(now + timedelta(hours=24)), "evaluated_at": iso(now),
            "prior_status": fields.get("Status"), "prior_evidence": fields.get("Evidence", ""),
            "capital_action": "NO ACTION"}


def market_decision(observation, now):
    f = observation["features"]
    extreme = f["volatility_annualized"] > 1.2 or f["max_drawdown_observed"] < -.65
    return {"id": "market:" + observation["symbol"], "name": observation["symbol"] + " — technical research lead",
            "symbol": observation["symbol"], "category": observation["category"], "origin": "technical_screen",
            "status": "REJECTED" if extreme else "NEEDS DATA",
            "reason": "Rejected by conservative research screen: extreme observed volatility/drawdown." if extreme else
                      "Price/volume anomaly identified; it is not a valuation, predictive edge or expected return.",
            "source": observation["source"], "source_sha256": observation["source_sha256"],
            "features": f, "currency": observation["currency"],
            "missing": [] if extreme else ["independent fundamental/catalyst research", "source cross-check",
                         "validated expected return and downside", "capital sizing", "entry/exit plan", "out-of-sample evidence"],
            "owner": "Research Agent", "review_at": iso(now + timedelta(hours=24)),
            "evaluated_at": iso(now), "capital_action": "NO ACTION"}


def screen(observations, now, limit=12):
    scored = []
    for o in observations:
        if o["status"] != "observed":
            continue
        f = o["features"]
        # Trigger thresholds are transparent screening heuristics, not probabilities.
        if abs(f["return_20d"]) >= .08 or (f["volume_ratio"] is not None and f["volume_ratio"] >= 1.8):
            scored.append((abs(f["return_20d"]) + max((f["volume_ratio"] or 0)-1, 0)*.05, o))
    scored.sort(key=lambda item: (-item[0], item[1]["symbol"]))
    return [market_decision(o, now) for _, o in scored[:limit]], len(scored)


def annual_facts(raw, now):
    data = json.loads(raw)
    facts = data.get("facts", {}).get("us-gaap", {})
    wanted = {
        "revenue": (("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"), "USD"),
        "net_income": (("NetIncomeLoss",), "USD"),
        "operating_cashflow": (("NetCashProvidedByUsedInOperatingActivities",), "USD"),
        "diluted_eps": (("EarningsPerShareDiluted",), "USD/shares"),
    }
    output = {}
    for name, (tags, unit) in wanted.items():
        for tag in tags:
            usable = []
            for fact in facts.get(tag, {}).get("units", {}).get(unit, []):
                try:
                    start, end = datetime.fromisoformat(fact["start"]), datetime.fromisoformat(fact["end"])
                    filed = datetime.fromisoformat(fact["filed"])
                    if (fact.get("form") == "10-K" and 330 <= (end-start).days <= 380
                            and filed.date() <= now.date() and end.date() <= now.date()
                            and math.isfinite(fact["val"])):
                        usable.append(fact)
                except (KeyError, ValueError, TypeError):
                    continue
            if usable:
                fact = max(usable, key=lambda f: (f["end"], f["filed"]))
                age = (now.date()-datetime.fromisoformat(fact["end"]).date()).days
                if age <= 550:
                    output[name] = {"value": fact["val"], "unit": unit, "period_end": fact["end"],
                                    "filed": fact["filed"], "accession": fact.get("accn"), "tag": tag}
                break
    return {"company": data.get("entityName"), "annual_facts": output}


def fundamental_scan(symbols, now, getter=fetch):
    if not symbols:
        return []
    registry_url = "https://www.sec.gov/files/company_tickers.json"
    try:
        registry = json.loads(getter(registry_url))
        ciks = {r["ticker"]: r["cik_str"] for r in registry.values()}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [{"symbol": s, "status": "unavailable", "source": registry_url, "error": str(exc)} for s in symbols]
    output = []
    for symbol in sorted(set(symbols)):
        if symbol not in ciks:
            output.append({"symbol": symbol, "status": "unavailable", "source": registry_url, "error": "No SEC ticker mapping"})
            continue
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(ciks[symbol]):010d}.json"
        try:
            raw = getter(url)
            data = annual_facts(raw, now)
            if not data["annual_facts"]:
                raise ValueError("No sufficiently recent usable US GAAP annual facts")
            output.append(dict(data, symbol=symbol, status="observed", source=url, observed_at=iso(now),
                               source_sha256=hashlib.sha256(raw.encode()).hexdigest()))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            output.append({"symbol": symbol, "status": "unavailable", "source": url, "error": str(exc)})
    return output


def run_mission(universe, backlog, previous=None, now=None, getter=fetch, workers=4):
    now = now or datetime.now(timezone.utc)
    cycle = str(uuid4())
    tasks = []
    previous = previous or {}
    task(tasks, cycle, "Commander Agent", "cycle", {"assigned_universe": sum(map(len, universe.values())),
         "backlog": len(backlog), "mode": "research_only"}, now)
    pairs = [(symbol, cat) for cat, symbols in universe.items() for symbol in symbols]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        observations = list(pool.map(lambda pair: history(*pair, now, getter), pairs))
    for o in observations:
        task(tasks, cycle, "Data Acquisition Agent", o["symbol"],
             {k:v for k,v in o.items() if k not in {"points", "features"}},
             now, "COMPLETED" if o["status"] == "observed" else "FAILED")
        if o["status"] == "observed":
            task(tasks, cycle, "Data Quality Agent", o["symbol"], {"freshness_limit_days": 5,
                 "usable_bars": o["features"]["bars"], "latest_bar": o["latest_bar"], "source_sha256": o["source_sha256"]}, now)
            task(tasks, cycle, "Feature Engineering Agent", o["symbol"], o["features"], now)
    tenders = tender_scan(now, getter)
    task(tasks, cycle, "Customer Agent", "CanadaBuys", {k:v for k,v in tenders.items() if k != "candidates"},
         now, "COMPLETED" if tenders["status"] == "observed" else "FAILED")
    market, triggered = screen(observations, now)
    stock_symbols = [d["symbol"] for d in market if d["category"] == "Stocks"]
    stock_symbols += [r["fields"]["Opportunity"].split(" ")[0] for r in backlog
                      if r["fields"].get("Category") == "Stocks" and "screening input" in r["fields"]["Opportunity"]]
    fundamentals = fundamental_scan(stock_symbols, now, getter)
    fundamental_by_symbol = {f["symbol"]: f for f in fundamentals if f["status"] == "observed"}
    for f in fundamentals:
        task(tasks, cycle, "Research Agent", f["symbol"], f, now,
             "COMPLETED" if f["status"] == "observed" else "FAILED")
        if f["status"] == "observed":
            task(tasks, cycle, "Due Diligence Agent", f["symbol"],
                 {"primary_source": f["source"], "annual_facts": f["annual_facts"],
                  "checked": "10-K duration, filing date, period age and numeric validity",
                  "limitations": "Automated extraction; reconciliation with full filing and recent quarters remains pending"}, now)
    task(tasks, cycle, "Discovery Agent", "multi-asset-screen", {"triggers": triggered,
         "researched_leads": len(market), "deferred_screen_triggers": max(triggered-len(market), 0)}, now)
    decisions = []
    old_decisions = previous.get("decisions", {})
    for record in backlog:
        d = review_backlog(record, now)
        # Never reopen a rejection automatically, and don't postpone an overdue SLA.
        old = old_decisions.get(d["id"], {})
        if old.get("review_at") and old.get("status") == d["status"]:
            d["review_at"] = old["review_at"]
        task(tasks, cycle, "Research Agent", d["name"], {"assessment": d["reason"], "missing": d["missing"]}, now)
        task(tasks, cycle, "Due Diligence Agent", d["name"], {"evidence_gate": "UNVERIFIED",
             "prior_claims_not_accepted": True, "missing": d["missing"]}, now)
        decisions.append(d)
    for d in market:
        if d["symbol"] in fundamental_by_symbol:
            d["fundamentals"] = fundamental_by_symbol[d["symbol"]]
            d["reason"] += " SEC annual financial facts retrieved; full thesis and recent-quarter review still required."
        task(tasks, cycle, "Quant Agent", d["name"], {"method": "descriptive 20/60-session returns; trailing realized risk",
             "features": d["features"], "predictive_validation": "NOT EXECUTED"}, now)
        task(tasks, cycle, "Risk Agent", d["name"], {"status": d["status"], "reason": d["reason"],
             "capital_action": d["capital_action"]}, now)
        decisions.append(d)
    for item in tenders["candidates"][:12]:
        too_close = item["days_remaining"] < 3
        d = dict(item, status="REJECTED" if too_close else "NEEDS DATA", origin="official_tender_screen",
                 reason="Insufficient sourcing/diligence window (<3 calendar days)." if too_close else
                        "Buyer demand observed; specifications, supplier compliance and margin remain unverified.",
                 missing=[] if too_close else ["official notice specifications", "supplier quote/authorization", "landed economics", "buyer payment terms"],
                 owner="Supplier Agent", review_at=iso(now+timedelta(hours=24)), evaluated_at=iso(now), capital_action="NO ACTION")
        task(tasks, cycle, "Opportunity Economics Agent", d["name"],
             {"economics": "UNAVAILABLE", "missing": d["missing"], "deadline_gate": d["reason"]}, now)
        decisions.append(d)
    for d in decisions:
        old = old_decisions.get(d["id"], {})
        if old.get("review_at") and old.get("status") == d["status"]:
            d["review_at"] = old["review_at"]
        d["sla_overdue"] = datetime.fromisoformat(d["review_at"]) < now and d["status"] == "NEEDS DATA"
        task(tasks, cycle, "Audit Agent", d["name"], {"decision": d["status"], "reason": d["reason"],
             "missing": d["missing"], "review_at": d["review_at"], "capital_action": "NO ACTION"}, now)
    # Keep historical candidates even when an anomaly no longer triggers.
    state_decisions = dict(old_decisions)
    state_decisions.update({d["id"]: d for d in decisions})
    due = [d["id"] for d in state_decisions.values() if d.get("status") == "NEEDS DATA"
           and datetime.fromisoformat(d["review_at"]) < now]
    task(tasks, cycle, "Monitoring Agent", "review-queue", {"overdue_ids": due, "open_decisions": len(state_decisions)}, now)
    task(tasks, cycle, "Research Archive Agent", "provenance", {"observed_sources": sum(o["status"] == "observed" for o in observations),
         "previous_cycle": previous.get("last_cycle"), "decisions_retained": len(state_decisions)}, now)
    outcomes = []
    observed = {o["symbol"]: o for o in observations if o["status"] == "observed"}
    for p in previous.get("observations_to_evaluate", []):
        if datetime.fromisoformat(p["due_at"]) <= now and p["symbol"] in observed:
            o = observed[p["symbol"]]
            if datetime.fromisoformat(o["latest_bar"]) > datetime.fromisoformat(p["observed_bar"]):
                outcomes.append(dict(p, actual_return=o["features"]["last"]/p["price"]-1,
                                     evaluated_at=iso(now), label="screen follow-up; not a predicted return"))
    task(tasks, cycle, "Learning Agent", "screen-follow-up", {"evaluated": len(outcomes),
         "outcomes": outcomes, "validated_model_changes": 0, "limitations": "No strategy return forecasts or backtests exist."}, now)
    pending = [p for p in previous.get("observations_to_evaluate", []) if not any(p["id"] == o["id"] for o in outcomes)]
    for d in market:
        if not any(p["symbol"] == d["symbol"] for p in pending):
            o = observed[d["symbol"]]
            pending.append({"id": cycle+":"+d["symbol"], "symbol": d["symbol"], "price": d["features"]["last"],
                            "observed_bar": o["latest_bar"], "due_at": iso(now+timedelta(days=7))})
    counts = {s: sum(d["status"] == s for d in decisions) for s in ("QUALIFIED", "REJECTED", "WATCHLIST", "NEEDS DATA")}
    successful = sum(t["status"] == "COMPLETED" for t in tasks)
    metrics = {"instruments_attempted": len(observations), "instruments_observed": len(observed),
               "procurement_rows_observed": tenders["rows_observed"], "screen_triggers": triggered,
               "backlog_reviewed": len(backlog), "decisions": len(decisions), **counts,
               "tasks_assigned": len(tasks), "tasks_completed": successful, "tasks_failed": len(tasks)-successful,
               "functional_workers_with_output": len({t["agent"] for t in tasks if t["status"] == "COMPLETED"}),
               "overdue_reviews": len(due), "outcomes_evaluated": len(outcomes), "capital_actions": 0}
    report = {"cycle_id": cycle, "version": VERSION, "started_at": iso(now), "completed_at": iso(datetime.now(timezone.utc)),
              "mode": "deterministic_research_workers", "metrics": metrics, "decisions": decisions,
              "tasks": tasks, "observations": observations, "procurement": tenders, "fundamentals": fundamentals, "outcomes": outcomes,
              "limitations": ["Single-provider technical observations; no independent cross-check or validated predictive edge.",
                             "31 registered roles are not 31 implemented autonomous analysts.",
                             "No smart-money feeds, live capital authority or verified portfolio balance.",
                             "NEEDS DATA triage is not completed fundamental/economic qualification."]}
    state = {"version": VERSION, "last_cycle": cycle, "decisions": state_decisions,
             "observations_to_evaluate": pending, "outcomes": previous.get("outcomes", []) + outcomes}
    return report, state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="state/mission.json")
    parser.add_argument("--output", default="reports/mission.json")
    parser.add_argument("--universe", default=str(ROOT/"config/universe.json"))
    parser.add_argument("--backlog", default=str(ROOT/"config/backlog.json"))
    args = parser.parse_args()
    state_path, output_path = Path(args.state), Path(args.output)
    old = json.loads(state_path.read_text()) if state_path.exists() else {}
    report, state = run_mission(json.loads(Path(args.universe).read_text()),
                                json.loads(Path(args.backlog).read_text()), old)
    for path, data in ((state_path, state), (output_path, report)):
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, indent=2))
        temp.replace(path)
    archive = output_path.parent/"cycles"/(report["cycle_id"]+".json")
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text(json.dumps(report, indent=2))
    print(json.dumps(report["metrics"]))
    if not report["metrics"]["instruments_observed"] and not report["metrics"]["procurement_rows_observed"]:
        raise SystemExit("No live discovery source succeeded; backlog triage only")


if __name__ == "__main__":
    main()
