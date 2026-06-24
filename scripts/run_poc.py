from q_rescue.services.response_service import compare_allocators
from q_rescue.simulation.generator import generate_scenario


def main() -> None:
    scenario = generate_scenario(ambulance_count=3, incident_count=5, seed=42)
    comparison = compare_allocators(scenario)
    print(f"Scenario: {scenario.name}")
    for name, payload in comparison.items():
        result = payload["result"]
        print(f"\n{name.upper()} ({result.solver_name})")
        print(f"Feasible: {result.feasible}")
        print(f"Objective: {result.objective_value:.3f}")
        print(f"Metrics: {payload['metrics']}")
        for assignment in result.assignments:
            print(
                f"  {assignment.ambulance_id} -> {assignment.incident_id} "
                f"({assignment.distance:.2f} km)"
            )


if __name__ == "__main__":
    main()
