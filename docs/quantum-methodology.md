# Quantum Methodology

## Decision variables

Let `x[a,i]` be 1 when ambulance `a` is assigned to incident `i`, otherwise 0.

## Initial POC objective

Minimise a weighted combination of travel distance and negative severity reward:

`C(x) = sum((w_d * distance[a,i] - w_s * severity[i]) * x[a,i])`

Let `K = min(number of ambulances, number of incidents)`. The assignment-count
penalty is:

`P_count(x) = lambda * (K - sum(x[a,i]))^2`

This prevents the optimiser from returning an artificially cheap solution that
leaves usable ambulances idle. For binary variables, `x^2 = x`, so this square
can be expanded directly into linear and quadratic QUBO coefficients.

Add collision penalties when:

- one ambulance is assigned to more than one incident;
- one incident receives more than one ambulance.

For every conflicting variable pair `(x_p, x_q)`:

`P_collision(x) = lambda * x_p * x_q`

The complete POC QUBO is:

`Q(x) = C(x) + P_count(x) + P_collision(x)`

The solver minimises `Q(x)`. Lower travel distance lowers the score, higher
severity lowers the score through its reward, and invalid assignments increase
the score through penalties.

## QAOA workflow

Qiskit converts the binary QUBO into an equivalent Ising Hamiltonian whose
lowest-energy state represents the best assignment. QAOA prepares and samples
an approximate low-energy state by alternating two circuit layers:

1. The cost layer applies phases based on the QUBO/Ising objective.
2. The mixer layer rotates the qubits so the algorithm can explore other binary
   assignments.

For `p` QAOA repetitions, the circuit has `2p` trainable angles. A classical
COBYLA optimiser repeatedly updates those angles using sampled objective values.
The best measured bit string is translated back into ambulance/incident
assignment variables.

Single-run QAOA configuration:

- QAOA repetitions (`reps`): 1
- Statevector sampler shots: 1024
- COBYLA maximum iterations: 100
- Random seed: 42
- Initial point: seeded non-zero angles in `[0, 2*pi)`, with length `2 * reps`

`StatevectorSampler` runs locally and samples from an ideal statevector. The
finite shot count still introduces sampling behaviour, but this is not a noisy
hardware experiment. Real-device execution and noise modelling are future work.

### Multi-start QAOA improvement

QAOA is a hybrid algorithm: a quantum circuit proposes sampled bit strings, and
a classical optimiser searches for good circuit angles. The final result can be
sensitive to the starting angles. A single unlucky seed can therefore produce a
valid but low-quality ambulance assignment.

To make the solver more reliable, the current comparison workflow can use
`MultiStartQAOASolver`. It runs QAOA several times with deterministic sub-seeds
derived from the main seed, evaluates every returned assignment with the same
QUBO energy function, and keeps the lowest-energy sample.

Default comparison setting:

- QAOA attempts (`--qaoa-attempts`): 4
- QAOA repetitions (`--reps`): 1
- Statevector sampler shots (`--shots`): 1024 by default, 2048 used in the
  latest small benchmark validation
- COBYLA maximum iterations (`--maxiter`): 100 by default, 50 used in the
  latest small benchmark validation

This improves solution quality but increases runtime roughly in proportion to
the number of attempts. Runtime optimisation is the next engineering task.

## Classical, exact, and QAOA comparison

All solvers must be evaluated on the same scenario and against the same QUBO.
The classical greedy allocator normally reports total travel distance, whereas
the quantum solvers report QUBO energy. These values are not directly
comparable. For a fair comparison, classical assignments are encoded as a
binary QUBO sample and evaluated with the same `Q(x)` equation.

The report keeps two categories of measurements separate:

- Operational metrics: average travel distance, incident coverage, critical
  coverage, assignment feasibility, and runtime.
- Optimisation metrics: QUBO energy and absolute/relative gap from the exact
  QUBO optimum.

Because valid QUBO energies can be negative, the relative gap is calculated as:

`100 * (solver_energy - exact_energy) / abs(exact_energy)`

This is reported as a percentage gap rather than as a conventional
approximation ratio, whose interpretation becomes confusing for negative
objectives.

### Progress timeline

The methodology deliberately keeps each stage of progress. The early weak QAOA
results are not removed, because they show what was learned and why the solver
was improved.

| Date/stage | What changed | Key outcome |
| --- | --- | --- |
| Week 1 synthetic POC | Built the first QUBO and ran single-start QAOA on a generated 3 ambulance / 5 incident problem. | QAOA produced a feasible assignment, but quality was worse than exact. |
| Sheffield benchmark integration | Connected the quantum workflow to Member 2's exported `scenario`, `distance_matrix`, and `severity_weights` files. | Single-start QAOA was still feasible, but much worse than exact on seed 42. |
| 22 June 2026 multi-start update | Added deterministic multi-start QAOA and kept the best QUBO energy across attempts. | QAOA matched exact enumeration on the small Sheffield benchmark, with higher runtime. |

### Stage 1: Week 1 synthetic POC result

Configuration: 3 ambulances, 5 incidents, 15 binary variables, grid coordinates,
seed 42, QAOA `reps=1`, 1024 shots, and COBYLA `maxiter=100`.

| Solver | QUBO energy | Runtime (local) | Average distance | Coverage | Critical coverage | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Classical greedy | -68.643651 | 0.000015 s | 3.785 km | 60% | 100% | Yes |
| Exact enumeration | -68.643651 | 0.485534 s | 3.785 km | 60% | 100% | Yes |
| QAOA simulator | -31.075298 | 5.644261 s | 10.975 km | 60% | 50% | Yes |

The classical and exact solvers selected the same assignments: `A1->I1`,
`A2->I2`, and `A3->I4`. QAOA selected `A1->I4`, `A2->I2`, and `A3->I3`.
Its absolute energy gap was `37.568353`, or `54.73%` relative to the exact
energy magnitude.

This result validates that the QUBO can be executed through QAOA and decoded
into a feasible emergency allocation. It does not demonstrate quantum
advantage: at this shallow circuit depth, QAOA produced a lower-quality result
and took longer than both classical methods on the small simulator problem.
Future experiments should test more repetitions, optimisers, initial points,
and seeds, while reporting all attempted configurations rather than selecting
only the best run.

### Stage 2: Sheffield benchmark single-start result

After Member 2's benchmark exports were integrated, the same comparison process
was run on the Sheffield flood response benchmark. This was an important
intermediate result because it showed that the QUBO pipeline worked with real
project inputs, but QAOA quality was still seed-sensitive.

Configuration: Sheffield flood response benchmark, 3 ambulances, 5 incidents,
15 binary variables, seed 42, QAOA `reps=1`, 1024 shots, COBYLA `maxiter=100`,
and one QAOA attempt.

| Solver | QUBO energy | Runtime (local) | Average distance | Coverage | Critical coverage | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Classical greedy | 11.532364 | 0.000015 s | 4.511 km | 60% | 100% | Yes |
| Exact enumeration | 9.987297 | 0.490767 s | 3.829 km | 60% | 100% | Yes |
| Single-start QAOA simulator | 22.132145 | 6.589727 s | 7.877 km | 60% | 100% | Yes |

Assignments:

- Classical greedy: `A1->I4`, `A2->I2`, `A3->I3`
- Exact enumeration: `A1->I4`, `A2->I1`, `A3->I5`
- Single-start QAOA: `A1->I5`, `A2->I4`, `A3->I1`

This was a valid but poor QAOA result. The QAOA gap from exact was `12.144848`,
or `121.60%`. That result motivated the multi-start improvement rather than
being hidden or overwritten.

### Stage 3: Current benchmark result, 22 June 2026

The solver has now been connected to Member 2's Sheffield benchmark exports:
`scenario.json`, `distance_matrix.json`, and `severity_weights.json`.

Command used for the latest validation:

```bash
.venv/bin/python scripts/compare_solvers.py \
  --benchmark-dir data/benchmarks/small \
  --reps 1 \
  --shots 2048 \
  --maxiter 50 \
  --seed 42 \
  --qaoa-attempts 4
```

Configuration: Sheffield flood response benchmark, 3 ambulances, 5 incidents,
15 binary variables, seed 42, QAOA `reps=1`, 2048 shots, COBYLA `maxiter=50`,
and 4 deterministic QAOA attempts.

| Solver | QUBO energy | Runtime (local) | Average distance | Coverage | Critical coverage | Feasible |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Classical greedy | 11.532364 | 0.000016 s | 4.511 km | 60% | 100% | Yes |
| Exact enumeration | 9.987297 | 0.456462 s | 3.829 km | 60% | 100% | Yes |
| Multi-start QAOA simulator | 9.987297 | 19.276596 s | 3.829 km | 60% | 100% | Yes |

Assignments:

- Classical greedy: `A1->I4`, `A2->I2`, `A3->I3`
- Exact enumeration: `A1->I4`, `A2->I1`, `A3->I5`
- Multi-start QAOA: `A1->I4`, `A2->I1`, `A3->I5`

Compared with the Stage 2 single-start result, multi-start QAOA reduced the
gap from `121.60%` to `0.00%` on the small benchmark by finding the same
assignment as exact enumeration. This is progress in solution quality, not yet
progress in runtime.

This is a strong correctness and quality result for the small proof of concept,
but it is not evidence of quantum advantage. Exact enumeration and greedy are
still faster at this scale. The next experiments must test larger scenarios,
runtime, repeated trials, and stronger classical baselines.

## Assumptions for the first POC

- Each ambulance serves at most one incident during one decision window.
- Each incident receives at most one ambulance.
- The model creates exactly `K` assignments when both input sets are non-empty.
- Severity is represented as `LOW=1`, `MEDIUM=2`, `HIGH=3`, `CRITICAL=4`.
- The synthetic Week 1 scenario used Euclidean distance.
- The Sheffield benchmark uses Member 2's exported distance matrix.
- Hospital capacity and routing are not yet part of the QUBO decision variables.

## Member 1 validation checklist

- Done: confirm penalty weights dominate invalid low-distance solutions.
- Done: compare exact QUBO and QAOA objective values on 3 ambulances / 5 incidents.
- Done: record QAOA reps, optimiser, shots, simulator backend, seed, and runtime.
- Done: report feasibility separately from objective quality.
- Done: connect the QUBO/QAOA workflow to Member 2's benchmark exports.
- Done: add multi-start QAOA to improve seed-sensitive results.
- Remaining: benchmark medium and large scenarios.
- Remaining: compare against stronger classical baselines beyond greedy.
- Remaining: tune runtime, attempts, shots, repetitions, and penalty weights.
- Remaining: test whether any quantum advantage claim is defensible.
- Remaining: document final hackathon experiment table.

## Next modelling decisions

Before the 30 June 2026 hackathon, the priority is experimentation rather than
adding many new variables. Hospital assignment, capacity, response-time
thresholds, and mandatory coverage can be represented with additional variables
or a staged optimisation pipeline, but they should be added only after the
ambulance assignment benchmarks are stable on small, medium, and large cases.
