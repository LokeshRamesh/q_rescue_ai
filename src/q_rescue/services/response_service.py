from q_rescue.classical.allocator import GreedyAllocator
from q_rescue.metrics.evaluator import calculate_metrics
from q_rescue.quantum.optimizer import QuantumAllocator
from q_rescue.simulation.generator import DisasterScenario
from q_rescue.simulation.distance_matrix import build_distance_matrix, build_severity_mapping


def compare_allocators(scenario: DisasterScenario) -> dict[str, dict[str, object]]:
    """Application service consumed by scripts, tests, and the dashboard."""
    distance_matrix = build_distance_matrix(scenario)
    severity_mapping = build_severity_mapping(scenario)

    results = {
        "classical": GreedyAllocator().solve(
            scenario.ambulances, scenario.incidents, distance_matrix, severity_mapping
        ),
        "quantum": QuantumAllocator().solve(
            scenario.ambulances, scenario.incidents, distance_matrix, severity_mapping
        ),
    }
    return {
        name: {"result": result, "metrics": calculate_metrics(result, scenario.incidents)}
        for name, result in results.items()
    }
