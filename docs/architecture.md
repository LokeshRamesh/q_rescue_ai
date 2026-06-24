# System Architecture

## Runtime flow

1. The simulation module produces ambulances, incidents, locations, and severity.
2. Shared domain models provide a stable contract between team modules.
3. Classical and quantum allocators consume the same scenario.
4. The metrics module evaluates both results using the same definitions.
5. The service layer prepares comparison data for Streamlit.

## Ownership boundaries

| Area | Owner | Public contract |
| --- | --- | --- |
| Simulation | Member 2 | `DisasterScenario` |
| Quantum optimisation | Member 1 | `QuantumAllocator.solve()` |
| Frontend | Member 3 | `compare_allocators()` output |
| Classical/integration | Member 4 | `GreedyAllocator.solve()` and tests |

The AI prediction layer belongs to the later MSc extension and should eventually
produce a risk-adjusted `DisasterScenario` without changing solver interfaces.

