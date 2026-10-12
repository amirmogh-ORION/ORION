# ORION Broker Layer

Paper trading first. Live trading requires explicit human authorization and separate configuration.

## IBKR Paper

1. Run **IB Gateway** logged into your **Paper Trading** account.
2. API settings:
   - Enable ActiveX and Socket Clients = ON
   - Read-Only API = **OFF**
   - Socket port = **4002**
3. From Python:

```python
from orion.broker import IBKRPaperBroker
from orion.portfolio import PortfolioEngine

broker = IBKRPaperBroker(port=4002)
broker.connect()
engine = PortfolioEngine(broker)
snap = engine.current_snapshot()
print(snap.cash, snap.equity, len(snap.positions))
broker.disconnect()
```

## Safety

- All orders go through `PortfolioEngine` risk limits.
- Default limits are sized for a ~$1,000 paper account.
- No live orders can be placed by this module.
