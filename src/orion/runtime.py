from __future__ import annotations
from dataclasses import dataclass
from uuid import uuid4
from .agents import AgentContext, Commander

@dataclass
class CycleResult:
    cycle_id: str
    reports: list

def run_cycle(commander: Commander, subjects: list[str]) -> CycleResult:
    cycle_id = str(uuid4())
    reports = commander.run_cycle(AgentContext(cycle_id=cycle_id, subjects=subjects))
    return CycleResult(cycle_id=cycle_id, reports=reports)
