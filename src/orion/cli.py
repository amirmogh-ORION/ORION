from .agents import Commander, StubAgent
from .runtime import run_cycle

def main() -> None:
    agents = [
        StubAgent("opportunity_scout", "Opportunity scan"),
        StubAgent("fundamental_analyst", "Fundamental"),
        StubAgent("quant_analyst", "Quantitative"),
        StubAgent("macro_analyst", "Macro/regime"),
        StubAgent("risk_manager", "Risk"),
        StubAgent("learning_agent", "Learning"),
    ]
    result = run_cycle(Commander(agents), ["SYSTEM_HEALTH"])
    print(f"ORION cycle {result.cycle_id}: {len(result.reports)} reports")

if __name__ == "__main__":
    main()
