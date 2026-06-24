# Team Workflow

## Suggested branches

- `feature/quantum-qubo-qaoa` - Member 1
- `feature/disaster-simulation` - Member 2
- `feature/streamlit-dashboard` - Member 3
- `feature/classical-integration` - Member 4

## Integration rules

1. Do not pass raw DataFrames between core modules; use domain models.
2. Keep solver-specific Qiskit types inside `q_rescue.quantum`.
3. Add a unit test for every objective or constraint change.
4. Use the same scenario and metrics for classical/quantum comparisons.
5. Merge small interface changes early instead of combining all modules in Week 3.

## Definition of done for the hackathon

- The 3-ambulance/5-incident POC is feasible and reproducible.
- Classical and quantum workflows use identical inputs.
- The dashboard displays assignments and comparison metrics.
- Tests cover QUBO constraints and end-to-end integration.
- The quantum methodology and known limitations are documented.

