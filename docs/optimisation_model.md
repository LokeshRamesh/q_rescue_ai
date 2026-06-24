# Optimisation Model Specification

## Problem Overview

Q-Rescue AI solves an **ambulance-to-incident assignment** problem for Sheffield emergency response. Given a set of ambulances at known locations and a set of active incidents with severity ratings, the system finds the optimal one-to-one assignment that minimises total weighted response cost.

---

## Decision Variables

Binary variable `xᵢⱼ ∈ {0, 1}` for every ambulance `i` and incident `j`:

```
xᵢⱼ = 1  →  ambulance i is assigned to incident j
xᵢⱼ = 0  →  no assignment
```

For a scenario with **A ambulances** and **I incidents**, there are **A × I** binary variables total.

**Example (3 ambulances, 5 incidents → 15 variables):**

| Variable | Meaning |
|----------|---------|
| x_{A1,I1} | Ambulance A1 → Incident I1 |
| x_{A1,I2} | Ambulance A1 → Incident I2 |
| x_{A2,I1} | Ambulance A2 → Incident I1 |
| … | … |

---

## Objective Function

Minimise the total severity-weighted response cost:

```
min  Σᵢ Σⱼ  [ w_d · d(aᵢ, iⱼ)  −  w_s · s(iⱼ) ]  ·  xᵢⱼ
```

Where:
- `d(aᵢ, iⱼ)` — distance (km) from ambulance `i` to incident `j`
- `s(iⱼ)` — numeric severity of incident `j` (see severity mapping below)
- `w_d` — `distance_weight` (default 1.0, configured in `configs/default.toml`)
- `w_s` — `severity_weight` (default 8.0, configured in `configs/default.toml`)

**Interpretation**: A lower cost means the ambulance is closer AND the incident is more severe. Subtracting severity ensures Critical incidents attract assignment.

---

## Operational Constraints

### C1: One ambulance per incident
Each incident receives at most one ambulance:
```
Σᵢ xᵢⱼ ≤ 1   ∀ j
```

### C2: One incident per ambulance
Each ambulance attends at most one incident per period:
```
Σⱼ xᵢⱼ ≤ 1   ∀ i
```

### C3: Hospital capacity
Total patients routed to hospital `h` must not exceed available beds:
```
Σ incidents(j) assigned to h ≤ available_beds(h)
```

### C4: Critical priority
Critical incidents (severity=4) are implicitly prioritised by the objective
function's severity weight. Optionally enforced as a hard constraint by
setting `critical_priority = true` in `OperationalConstraints`.

---

## Severity Weight Mapping

Two severity schemes are used, both producing the same **relative ordering**:

| Severity | IntEnum value | QUBO weight (×8.0) | Spec absolute weight | Absolute / QUBO |
|----------|:---:|:---:|:---:|:---:|
| LOW | 1 | 8 | 25 | ~3.1× |
| MEDIUM | 2 | 16 | 50 | ~3.1× |
| HIGH | 3 | 24 | 75 | ~3.1× |
| CRITICAL | 4 | 32 | 100 | ~3.1× |

> **Design decision**: The QUBO solver uses the `Severity` IntEnum (1–4) scaled
> by `severity_weight=8.0` from `configs/default.toml`. This preserves the
> exact relative ordering of the spec's absolute weights (25/50/75/100) while
> keeping QUBO penalty coefficients manageable. The `Severity.absolute_weight()`
> method is provided for exports, documentation, and dashboard display.

---

## QUBO Encoding

For the quantum optimisation module (Member 1), constraints C1 and C2 are
encoded as quadratic penalty terms added to the objective:

```
QUBO = Objective + λ · Σ constraint_violations
```

Where `λ = constraint_penalty` (default 100.0). The penalty ensures that any
infeasible assignment has a higher QUBO energy than any feasible one.

See `src/q_rescue/quantum/qubo.py` (`AmbulanceAllocationQuboBuilder`) for
the full QUBO matrix construction.

---

## Scalability Notes

| Ambulances | Incidents | Binary variables | Feasibility for exact QUBO |
|:---:|:---:|:---:|:---|
| 3 | 5 | 15 | ✅ Exact solver (all 2¹⁵ = 32,768 states) |
| 4 | 6 | 24 | ✅ Exact solver limit |
| 5 | 8 | 40 | ⚠️ Requires QAOA or simulated annealing |
| 10 | 20 | 200 | ❌ Classical exact solver infeasible |

The dashboard enforces the 24-variable limit when using the exact solver.
Member 1's Qiskit QAOA solver is available for larger scenarios, with
multi-start QAOA used in benchmarks when solution quality is more important
than runtime. Medium and large benchmark validation is still required before
making performance or quantum-advantage claims.
