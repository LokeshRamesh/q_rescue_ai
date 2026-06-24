from q_rescue.services.response_service import compare_allocators
from q_rescue.simulation.generator import generate_scenario


def test_poc_comparison_runs_end_to_end() -> None:
    scenario = generate_scenario(ambulance_count=2, incident_count=3, seed=7)

    comparison = compare_allocators(scenario)

    assert set(comparison) == {"classical", "quantum"}
    assert comparison["quantum"]["result"].feasible
