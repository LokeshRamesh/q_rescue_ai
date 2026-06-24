from q_rescue.simulation.scenarios import generate_scenario_by_category
from q_rescue.domain.models import DisasterCategory
from q_rescue.simulation.distance_matrix import build_distance_matrix, build_severity_mapping
from q_rescue.classical.allocator import GreedyAllocator
from q_rescue.quantum.qubo import AmbulanceAllocationQuboBuilder


def test_simulation_consumable_by_classical_allocator():
    scenario = generate_scenario_by_category(DisasterCategory.FLOOD)
    dm = build_distance_matrix(scenario)
    sm = build_severity_mapping(scenario)

    allocator = GreedyAllocator()

    # The classical allocator should be able to process the scenario
    # without raising exceptions.
    result = allocator.solve(scenario.ambulances, scenario.incidents, dm, sm)

    assert result.feasible is True
    # In a greedy allocation, every ambulance gets used if incidents >= ambulances
    assert len(result.assignments) == min(len(scenario.ambulances), len(scenario.incidents))


def test_simulation_consumable_by_qubo_builder():
    scenario = generate_scenario_by_category(DisasterCategory.INDUSTRIAL_ACCIDENT)
    dm = build_distance_matrix(scenario)
    sm = build_severity_mapping(scenario)

    builder = AmbulanceAllocationQuboBuilder()

    # The QUBO builder should be able to process the scenario directly
    model = builder.build(scenario.ambulances, scenario.incidents, dm, sm)

    # Check binary variable count (ambulances * incidents)
    expected_vars = len(scenario.ambulances) * len(scenario.incidents)
    assert len(model.variables) == expected_vars
