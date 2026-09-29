from __future__ import annotations
from dataclasses import dataclass
from uuid import uuid4
from .agents import AgentContext, Commander
from .learning import load_active_rules

@dataclass
class CycleResult:
    cycle_id: str
    reports: list

def run_cycle(commander: Commander, subjects: list[str]) -> CycleResult:
    cycle_id = str(uuid4())
    learned_rules = tuple(rule.rule for rule in load_active_rules())
    reports = commander.run_cycle(
        AgentContext(
            cycle_id=cycle_id,
            subjects=subjects,
            active_rules=learned_rules,
        )
    )
    return CycleResult(cycle_id=cycle_id, reports=reports)
