from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .domain import AgentReport, Evidence

@dataclass(frozen=True)
class AgentContext:
    cycle_id: str
    subjects: list[str]
    active_rules: tuple[str, ...] = ()

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
    def __init__(self, agents: list[Agent]):
        if not agents:
            raise ValueError("Commander requires at least one agent")
        self.agents = agents

    def run_cycle(self, context: AgentContext) -> list[AgentReport]:
        reports: list[AgentReport] = []
        for agent in self.agents:
            reports.extend(agent.run(context))
        return reports
