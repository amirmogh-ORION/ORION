from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .domain import AgentReport, Evidence

@dataclass(frozen=True)
class AgentContext:
    cycle_id: str
    subjects: list[str]
    active_rules: tuple[str, ...] = ()

@dataclass(frozen=True)
class CommanderDecision:
    subject: str
    state: str
    confidence: float
    rationale: str
    agents_consulted: tuple[str, ...]
    disagreements: tuple[str, ...]
    risk_veto: bool

class Agent(ABC):
    name: str

    @abstractmethod
    def run(self, context: AgentContext) -> list[AgentReport]:
        raise NotImplementedError

class StubAgent(Agent):
    def __init__(self, name: str, role: str):
        self.name, self.role = name, role

    def run(self, context: AgentContext) -> list[AgentReport]:
        return [
            AgentReport(
                agent=self.name,
                subject=subject,
                conclusion=f"{self.role} analysis pending live data connector",
                confidence=0.0,
                evidence=[Evidence(
                    source="internal",
                    claim=f"No external market data was used in this cycle; {len(context.active_rules)} active learned rules were loaded",
                    reliability=1.0,
                )],
            )
            for subject in context.subjects
        ]

class Commander:
    """Orchestrates specialists and synthesizes; never silently resolves disagreement."""

    def __init__(self, agents: list[Agent]):
        if not agents:
            raise ValueError("Commander requires at least one agent")
        self.agents = agents

    def run_cycle(self, context: AgentContext) -> list[AgentReport]:
        reports: list[AgentReport] = []
        for agent in self.agents:
            reports.extend(agent.run(context))
        return reports

    def synthesize(self, reports: list[AgentReport]) -> list[CommanderDecision]:
        by_subject: dict[str, list[AgentReport]] = {}
        for report in reports:
            by_subject.setdefault(report.subject, []).append(report)
        decisions = []
        for subject, subject_reports in sorted(by_subject.items()):
            agents = tuple(sorted({r.agent for r in subject_reports}))
            conclusions = tuple(sorted({r.conclusion.strip() for r in subject_reports}))
            risk_reports = [r for r in subject_reports if "risk" in r.agent.casefold()]
            risk_veto = any(self._vote(r.conclusion) in {"REJECT", "VETO"} for r in risk_reports)
            votes = tuple(self._vote(r.conclusion) for r in subject_reports)
            actionable = tuple(v for v in votes if v in {"APPROVE", "REJECT", "VETO"})
            disagreement = len(set(actionable)) > 1
            verified = all(r.evidence and all(e.reliability >= 0.8 for e in r.evidence) for r in subject_reports)
            if risk_veto:
                state, rationale = "NO_ACTION", "Risk specialist vetoed the proposal."
            elif disagreement:
                state, rationale = "NO_ACTION", "Specialist disagreement remains unresolved."
            elif not verified:
                state, rationale = "NO_ACTION", "Evidence gate failed."
            elif actionable and set(actionable) == {"APPROVE"}:
                state, rationale = "SHADOW_APPROVED", "All actionable specialist conclusions approve."
            else:
                state, rationale = "NO_ACTION", "No unanimous evidence-backed approval."
            decisions.append(CommanderDecision(
                subject=subject, state=state,
                confidence=min((r.confidence for r in subject_reports), default=0.0),
                rationale=rationale, agents_consulted=agents,
                disagreements=conclusions if disagreement else (), risk_veto=risk_veto,
            ))
        return decisions

    @staticmethod
    def _vote(conclusion: str) -> str:
        token = conclusion.strip().upper().split(":", 1)[0]
        return token if token in {"APPROVE", "REJECT", "VETO"} else "ABSTAIN"
