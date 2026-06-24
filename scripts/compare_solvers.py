from __future__ import annotations

import argparse
from pathlib import Path

from q_rescue.quantum.comparison import (
    ComparisonReport,
    SolverBenchmark,
    compare_benchmark_exports,
    compare_solvers,
)
from q_rescue.quantum.qaoa_solver import MultiStartQAOASolver, QiskitQAOASolver
from q_rescue.simulation.generator import generate_scenario


def main() -> None:
    args = _parse_args()
    qaoa_solver = _build_qaoa_solver(args)

    if args.benchmark_dir:
        report = compare_benchmark_exports(
            args.benchmark_dir,
            qaoa_solver=qaoa_solver,
        )
    else:
        scenario = generate_scenario(
            ambulance_count=args.ambulances,
            incident_count=args.incidents,
            seed=args.seed,
            use_sheffield_coords=False,
        )
        report = compare_solvers(
            scenario,
            qaoa_solver=qaoa_solver,
        )
    _print_report(report)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Q-Rescue allocation solvers")
    parser.add_argument("--ambulances", type=int, default=3)
    parser.add_argument("--incidents", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--maxiter", type=int, default=100)
    parser.add_argument(
        "--qaoa-attempts",
        type=int,
        default=4,
        help="Number of deterministic QAOA starts to try before keeping the best solution",
    )
    parser.add_argument(
        "--benchmark-dir",
        type=Path,
        help="Directory containing Member 2 benchmark JSON exports",
    )
    return parser.parse_args()


def _build_qaoa_solver(args: argparse.Namespace) -> QiskitQAOASolver | MultiStartQAOASolver:
    if args.qaoa_attempts == 1:
        return QiskitQAOASolver(
            reps=args.reps,
            shots=args.shots,
            seed=args.seed,
            maxiter=args.maxiter,
        )
    return MultiStartQAOASolver(
        reps=args.reps,
        shots=args.shots,
        seed=args.seed,
        maxiter=args.maxiter,
        attempts=args.qaoa_attempts,
    )


def _print_report(report: ComparisonReport) -> None:
    print(f"Scenario: {report.scenario_name}")
    print(f"Binary variables: {report.binary_variables}")
    print()
    print(
        f"{'Solver':<20} {'QUBO energy':>12} {'Runtime (s)':>12} "
        f"{'Avg distance':>14} {'Coverage':>10} {'Critical':>10} {'Feasible':>10}"
    )
    print("-" * 104)
    for benchmark in (report.classical, report.exact, report.qaoa):
        _print_benchmark(benchmark)

    print()
    print(
        f"Classical gap from exact: {report.classical_gap:.6f} "
        f"({report.classical_relative_gap_percent:.2f}%)"
    )
    print(f"QAOA gap from exact: {report.qaoa_gap:.6f} ({report.qaoa_relative_gap_percent:.2f}%)")

    for benchmark in (report.classical, report.exact, report.qaoa):
        assignments = ", ".join(
            f"{item.ambulance_id}->{item.incident_id}" for item in benchmark.assignments
        )
        print(f"{benchmark.solver_name} assignments: {assignments}")


def _print_benchmark(benchmark: SolverBenchmark) -> None:
    metrics = benchmark.metrics
    print(
        f"{benchmark.solver_name:<20} {benchmark.qubo_energy:>12.6f} "
        f"{benchmark.runtime_seconds:>12.6f} {metrics['average_distance_km']:>14.3f} "
        f"{metrics['coverage_percent']:>9.1f}% "
        f"{metrics['critical_coverage_percent']:>9.1f}% "
        f"{str(benchmark.feasible):>10}"
    )


if __name__ == "__main__":
    main()
