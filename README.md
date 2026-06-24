# Q-Rescue AI

Q-Rescue AI is a hackathon prototype for simulating a disaster and comparing
classical emergency-resource allocation with a QUBO-based quantum workflow.

## Architecture

```text
Simulation -> Optimisation model -> Classical / Quantum solvers -> Metrics -> Dashboard
```

The code is split by team ownership while sharing stable domain models:

- `src/q_rescue/simulation/`: Member 2, disaster scenarios and synthetic data.
- `src/q_rescue/classical/`: Member 4, greedy baseline allocation.
- `src/q_rescue/quantum/`: Member 1, QUBO formulation and QAOA integration.
- `app/`: Member 3, Streamlit dashboard and visualisation.
- `src/q_rescue/services/`: integration layer connecting all modules.
- `tests/`: unit and future integration tests.
- `docs/`: architecture, quantum methodology, and team workflow.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python scripts/run_poc.py
pytest
```

For the dashboard and core dependencies:

```bash
pip install -e .
streamlit run app/streamlit_app.py
```

Install Qiskit separately when working on Member 1's QAOA adapter:

```bash
pip install -e ".[quantum,dev]"
```

## Member 1 starting points

1. Refine `AmbulanceAllocationQuboBuilder` in `src/q_rescue/quantum/qubo.py`.
2. Implement `QiskitQAOASolver` in `src/q_rescue/quantum/qaoa_solver.py`.
3. Validate the 3-ambulance/5-incident POC with `scripts/run_poc.py`.
4. Compare feasibility, objective value, response time, and critical coverage.
5. Record equations and experimental settings in `docs/quantum-methodology.md`.

See `docs/team-workflow.md` for suggested branch and interface ownership.

