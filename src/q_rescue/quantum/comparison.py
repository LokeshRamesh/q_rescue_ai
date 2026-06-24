from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from q_rescue.classical.allocator import GreedyAllocator
from q_rescue.domain.models import (
    Ambulance,
    Assignment,
    DisasterCategory,
    Hospital,
    Incident,
    Location,
    OptimizationResult,
    Severity,
)
from q_rescue.metrics.evaluator import calculate_metrics
from q_rescue.quantum.qaoa_solver import ExactQuboSolver, QiskitQAOASolver, QuboSolver
from q_rescue.quantum.qubo import AmbulanceAllocationQuboBuilder, QuboModel, Variable
from q_rescue.simulation.distance_matrix import DistanceMatrix, SeverityMapping
from q_rescue.simulation.generator import DisasterScenario
from q_rescue.simulation.distance_matrix import build_distance_matrix, build_severity_mapping


@dataclass(frozen=True)
class SolverBenchmark:
    solver_name: str
    runtime_seconds: float
    qubo_energy: float
    assignments: list[Assignment]
    feasible: bool
    metrics: dict[str, float]


@dataclass(frozen=True)
class ComparisonReport:
    scenario_name: str
    binary_variables: int
    classical: SolverBenchmark
    exact: SolverBenchmark
    qaoa: SolverBenchmark
    classical_gap: float
    qaoa_gap: float
    classical_relative_gap_percent: float
    qaoa_relative_gap_percent: float


def compare_solvers(
    scenario: DisasterScenario,
    *,
    builder: AmbulanceAllocationQuboBuilder | None = None,
    qaoa_solver: QuboSolver | None = None,
) -> ComparisonReport:
    """Benchmark classical, exact-QUBO, and QAOA solvers on one scenario."""
    builder = builder or AmbulanceAllocationQuboBuilder()
    qaoa_solver = qaoa_solver or QiskitQAOASolver()
    distance_matrix = build_distance_matrix(scenario)
    severity_mapping = build_severity_mapping(scenario)

    model = builder.build(
        scenario.ambulances, scenario.incidents, distance_matrix, severity_mapping
    )

    classical = _benchmark_classical(scenario, model, distance_matrix, severity_mapping)
    exact = _benchmark_qubo_solver(scenario, model, ExactQuboSolver(), distance_matrix)
    qaoa = _benchmark_qubo_solver(scenario, model, qaoa_solver, distance_matrix)

    classical_gap = classical.qubo_energy - exact.qubo_energy
    qaoa_gap = qaoa.qubo_energy - exact.qubo_energy
    denominator = max(abs(exact.qubo_energy), 1e-12)

    return ComparisonReport(
        scenario_name=scenario.name,
        binary_variables=len(model.variables),
        classical=classical,
        exact=exact,
        qaoa=qaoa,
        classical_gap=classical_gap,
        qaoa_gap=qaoa_gap,
        classical_relative_gap_percent=100.0 * classical_gap / denominator,
        qaoa_relative_gap_percent=100.0 * qaoa_gap / denominator,
    )


def compare_benchmark_exports(
    benchmark_dir: Path,
    *,
    builder: AmbulanceAllocationQuboBuilder | None = None,
    qaoa_solver: QuboSolver | None = None,
) -> ComparisonReport:
    """Benchmark solvers against Member 2's exported benchmark JSON files."""
    scenario, distance_matrix, severity_mapping = load_benchmark_exports(benchmark_dir)
    return compare_solvers_with_inputs(
        scenario,
        distance_matrix,
        severity_mapping,
        builder=builder,
        qaoa_solver=qaoa_solver,
    )


def compare_solvers_with_inputs(
    scenario: DisasterScenario,
    distance_matrix: DistanceMatrix,
    severity_mapping: SeverityMapping,
    *,
    builder: AmbulanceAllocationQuboBuilder | None = None,
    qaoa_solver: QuboSolver | None = None,
) -> ComparisonReport:
    """Benchmark solvers using pre-computed simulation outputs."""
    builder = builder or AmbulanceAllocationQuboBuilder()
    qaoa_solver = qaoa_solver or QiskitQAOASolver()
    model = builder.build(
        scenario.ambulances, scenario.incidents, distance_matrix, severity_mapping
    )

    classical = _benchmark_classical(scenario, model, distance_matrix, severity_mapping)
    exact = _benchmark_qubo_solver(scenario, model, ExactQuboSolver(), distance_matrix)
    qaoa = _benchmark_qubo_solver(scenario, model, qaoa_solver, distance_matrix)

    classical_gap = classical.qubo_energy - exact.qubo_energy
    qaoa_gap = qaoa.qubo_energy - exact.qubo_energy
    denominator = max(abs(exact.qubo_energy), 1e-12)

    return ComparisonReport(
        scenario_name=scenario.name,
        binary_variables=len(model.variables),
        classical=classical,
        exact=exact,
        qaoa=qaoa,
        classical_gap=classical_gap,
        qaoa_gap=qaoa_gap,
        classical_relative_gap_percent=100.0 * classical_gap / denominator,
        qaoa_relative_gap_percent=100.0 * qaoa_gap / denominator,
    )


def load_benchmark_exports(
    benchmark_dir: Path,
) -> tuple[DisasterScenario, DistanceMatrix, SeverityMapping]:
    """Load Member 2's exported scenario, distance matrix, and severity mapping."""
    scenario_data = _read_json(benchmark_dir / "scenario.json")
    distance_data = _read_json(benchmark_dir / "distance_matrix.json")
    severity_data = _read_json(benchmark_dir / "severity_weights.json")

    scenario = DisasterScenario(
        name=str(scenario_data["name"]),
        ambulances=[
            Ambulance(
                id=str(item["id"]),
                location=Location(float(item["lat"]), float(item["lon"])),
                status=str(item.get("status", "available")).capitalize(),
            )
            for item in scenario_data["ambulances"]
        ],
        incidents=[
            Incident(
                id=str(item["id"]),
                location=Location(float(item["lat"]), float(item["lon"])),
                severity=Severity[str(item["severity_level"])],
                category=DisasterCategory(str(scenario_data["category"])),
            )
            for item in scenario_data["incidents"]
        ],
        hospitals=[
            Hospital(
                id=str(item["id"]),
                name=str(item["name"]),
                location=Location(float(item["lat"]), float(item["lon"])),
                capacity=int(item["capacity"]),
                available_beds=int(item["available_beds"]),
            )
            for item in scenario_data["hospitals"]
        ],
        category=DisasterCategory(str(scenario_data["category"])),
    )
    distance_matrix = DistanceMatrix(
        matrix={
            str(ambulance_id): {
                str(incident_id): float(distance)
                for incident_id, distance in incident_distances.items()
            }
            for ambulance_id, incident_distances in distance_data.items()
        },
        ambulance_ids=[ambulance.id for ambulance in scenario.ambulances],
        incident_ids=[incident.id for incident in scenario.incidents],
    )
    severity_mapping = {
        str(incident_id): int(weight) for incident_id, weight in severity_data.items()
    }
    return scenario, distance_matrix, severity_mapping


def sample_from_assignments(
    model: QuboModel,
    assignments: list[Assignment],
) -> dict[Variable, int]:
    """Encode assignments as a complete binary sample for shared QUBO evaluation."""
    sample = {variable: 0 for variable in model.variables}
    for assignment in assignments:
        variable = (assignment.ambulance_id, assignment.incident_id)
        if variable not in sample:
            raise ValueError(f"Assignment {variable!r} is not present in the QUBO")
        sample[variable] = 1
    return sample


def _read_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _benchmark_classical(
    scenario: DisasterScenario,
    model: QuboModel,
    distance_matrix: DistanceMatrix,
    severity_mapping: SeverityMapping,
) -> SolverBenchmark:
    started = perf_counter()
    result = GreedyAllocator().solve(
        scenario.ambulances, scenario.incidents, distance_matrix, severity_mapping
    )
    runtime = perf_counter() - started
    sample = sample_from_assignments(model, result.assignments)
    return _build_benchmark(scenario, model, sample, result.solver_name, runtime, distance_matrix)


def _benchmark_qubo_solver(
    scenario: DisasterScenario,
    model: QuboModel,
    solver: QuboSolver,
    distance_matrix: DistanceMatrix,
) -> SolverBenchmark:
    started = perf_counter()
    sample, _ = solver.solve(model)
    runtime = perf_counter() - started
    return _build_benchmark(scenario, model, sample, solver.name, runtime, distance_matrix)


def _build_benchmark(
    scenario: DisasterScenario,
    model: QuboModel,
    sample: dict[Variable, int],
    solver_name: str,
    runtime_seconds: float,
    distance_matrix: DistanceMatrix,
) -> SolverBenchmark:
    assignments = [
        Assignment(
            ambulance_id=ambulance_id,
            incident_id=incident_id,
            distance=distance_matrix.matrix[ambulance_id][incident_id],
        )
        for (ambulance_id, incident_id), selected in sample.items()
        if selected
    ]
    feasible = _is_feasible(assignments, scenario)
    result = OptimizationResult(
        assignments=assignments,
        objective_value=model.evaluate(sample),
        solver_name=solver_name,
        feasible=feasible,
    )
    return SolverBenchmark(
        solver_name=solver_name,
        runtime_seconds=runtime_seconds,
        qubo_energy=result.objective_value,
        assignments=assignments,
        feasible=feasible,
        metrics=calculate_metrics(result, scenario.incidents),
    )


def _is_feasible(assignments: list[Assignment], scenario: DisasterScenario) -> bool:
    target = min(len(scenario.ambulances), len(scenario.incidents))
    ambulance_ids = [assignment.ambulance_id for assignment in assignments]
    incident_ids = [assignment.incident_id for assignment in assignments]
    return (
        len(assignments) == target
        and len(ambulance_ids) == len(set(ambulance_ids))
        and len(incident_ids) == len(set(incident_ids))
    )
