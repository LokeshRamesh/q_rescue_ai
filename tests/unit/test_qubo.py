from q_rescue.domain.models import Ambulance, Incident, Location, Severity
from q_rescue.quantum.qaoa_solver import ExactQuboSolver
from q_rescue.quantum.qubo import AmbulanceAllocationQuboBuilder
from q_rescue.simulation.distance_matrix import DistanceMatrix


def _mock_data():
    ambulances = [Ambulance("A1", Location(0, 0)), Ambulance("A2", Location(1, 1))]
    incidents = [
        Incident("I1", Location(2, 2), Severity.CRITICAL),
        Incident("I2", Location(3, 3), Severity.LOW),
    ]
    dm = DistanceMatrix(
        matrix={
            "A1": {"I1": 0.5, "I2": 20.0},
            "A2": {"I1": 15.0, "I2": 25.0},
        },
        ambulance_ids=["A1", "A2"],
        incident_ids=["I1", "I2"],
    )
    sm = {"I1": 100, "I2": 25}
    return ambulances, incidents, dm, sm


def test_qubo_contains_one_variable_per_candidate_assignment() -> None:
    ambulances, incidents, dm, sm = _mock_data()

    model = AmbulanceAllocationQuboBuilder().build(ambulances, incidents, dm, sm)

    assert len(model.variables) == 4
    assert ("A1", "I1") in model.variables


def test_exclusion_penalty_discourages_duplicate_ambulance_use() -> None:
    ambulances, incidents, dm, sm = _mock_data()
    model = AmbulanceAllocationQuboBuilder(constraint_penalty=1000).build(
        ambulances, incidents, dm, sm
    )

    single = model.evaluate({("A1", "I1"): 1, ("A1", "I2"): 0})
    duplicate = model.evaluate({("A1", "I1"): 1, ("A1", "I2"): 1})

    assert duplicate > single


def test_exact_solver_returns_a_feasible_low_cost_sample() -> None:
    ambulances, incidents, dm, sm = _mock_data()
    # Trim to 1x1 for this test
    ambulances = ambulances[:1]
    incidents = incidents[:1]
    model = AmbulanceAllocationQuboBuilder().build(ambulances, incidents, dm, sm)

    sample, value = ExactQuboSolver().solve(model)

    assert sample[("A1", "I1")] == 1
    # Check if objective is negative as intended by cost formula
    assert value < 0


def test_solver_uses_all_available_ambulances_when_incidents_are_available() -> None:
    ambulances = [
        Ambulance("A1", Location(0, 0)),
        Ambulance("A2", Location(10, 0)),
    ]
    incidents = [
        Incident("I1", Location(1, 0), Severity.LOW),
        Incident("I2", Location(9, 0), Severity.LOW),
        Incident("I3", Location(100, 100), Severity.LOW),
    ]
    dm = DistanceMatrix(
        matrix={
            "A1": {"I1": 1, "I2": 9, "I3": 100},
            "A2": {"I1": 9, "I2": 1, "I3": 90},
        },
        ambulance_ids=["A1", "A2"],
        incident_ids=["I1", "I2", "I3"],
    )
    sm = {"I1": 25, "I2": 25, "I3": 25}

    model = AmbulanceAllocationQuboBuilder().build(ambulances, incidents, dm, sm)

    sample, _ = ExactQuboSolver().solve(model)

    assert sum(sample.values()) == 2


def test_solver_prioritises_critical_incident_when_resources_are_scarce() -> None:
    ambulances = [Ambulance("A1", Location(0, 0))]
    incidents = [
        Incident("I-low", Location(1, 0), Severity.LOW),
        Incident("I-critical", Location(2, 0), Severity.CRITICAL),
    ]
    dm = DistanceMatrix(
        matrix={"A1": {"I-low": 1.0, "I-critical": 2.0}},
        ambulance_ids=["A1"],
        incident_ids=["I-low", "I-critical"],
    )
    sm = {"I-low": 25, "I-critical": 100}

    model = AmbulanceAllocationQuboBuilder(
        distance_weight=1.0,
        severity_weight=10.0,
    ).build(ambulances, incidents, dm, sm)

    sample, _ = ExactQuboSolver().solve(model)

    assert sample[("A1", "I-critical")] == 1
    assert sample[("A1", "I-low")] == 0
