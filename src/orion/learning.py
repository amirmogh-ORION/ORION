from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ActiveRule:
    name: str
    domain: str
    version: str
    rule: str
    evidence: str


def load_active_rules() -> list[ActiveRule]:
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("ORION_AIRTABLE_BASE_ID", "apphGZmtffjzQt3C3")
    if not token:
        return []

    table = quote("Rules & Models", safe="")
    params = urlencode({"filterByFormula": "{Status}='ACTIVE'"})
    url = f"https://api.airtable.com/v0/{base_id}/{table}?{params}"

    records: list[dict] = []
    while url:
        req = Request(url, headers={"Authorization": f"Bearer {token}"})
        with urlopen(req, timeout=10) as resp:
            payload = json.load(resp)
        records.extend(payload.get("records", []))
        offset = payload.get("offset")
        if offset:
            url = f"https://api.airtable.com/v0/{base_id}/{table}?{params}&offset={quote(offset)}"
        else:
            url = ""

    rules: list[ActiveRule] = []
    for record in records:
        fields = record.get("fields", {})
        text = str(fields.get("Rule", "")).strip()
        if not text:
            continue
        rules.append(
            ActiveRule(
                name=str(fields.get("Rule/Model", "")).strip(),
                domain=str(fields.get("Domain", "")).strip(),
                version=str(fields.get("Version", "")).strip(),
                rule=text,
                evidence=str(fields.get("Evidence", "")).strip(),
            )
        )
    return rules
