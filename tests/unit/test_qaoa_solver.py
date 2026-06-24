import pytest

pytest.importorskip("qiskit_optimization")

from q_rescue.domain.models import Ambulance, Incident, Location, Severity
from q_rescue.quantum.qaoa_solver import ExactQuboSolver, QiskitQAOASolver
from q_rescue.quantum.qubo import AmbulanceAllocationQuboBuilder, QuboModel
from q_rescue.simulation.distance_matrix import build_distance_matrix, build_severity_mapping
from q_rescue.simulation.generator import DisasterScenario


def test_qaoa_selects_single_beneficial_assignment() -> None:
    variable = ("A1", "I1")
    model = QuboModel(linear={variable: -3.0})

    sample, value = QiskitQAOASolver(shots=256, maxiter=20).solve(model)

    assert sample == {variable: 1}
    assert value == pytest.approx(-3.0)


def test_qaoa_matches_exact_solver_on_small_ambulance_problem() -> None:
    ambulances = [Ambulance("A1", Location(0.0, 0.0))]
    incidents = [
        Incident("I-low", Location(0.001, 0.0), Severity.LOW),
        Incident("I-critical", Location(0.002, 0.0), Severity.CRITICAL),
    ]
    scenario = DisasterScenario(
        name="test", ambulances=ambulances, incidents=incidents, hospitals=[]
    )
    dm = build_distance_matrix(scenario)
    sm = build_severity_mapping(scenario)
    model = AmbulanceAllocationQuboBuilder().build(ambulances, incidents, dm, sm)

    exact_sample, exact_value = ExactQuboSolver().solve(model)
    qaoa_sample, qaoa_value = QiskitQAOASolver(shots=1024, maxiter=50).solve(model)

    assert qaoa_sample == exact_sample
    assert qaoa_value == pytest.approx(exact_value)


def test_qaoa_returns_complete_binary_sample() -> None:
    variables = [("A1", "I1"), ("A1", "I2")]
    model = QuboModel(linear={variables[0]: -2.0, variables[1]: 1.0})

    sample, _ = QiskitQAOASolver(shots=256, maxiter=20).solve(model)

    assert set(sample) == set(variables)
    assert set(sample.values()) <= {0, 1}


def test_seeded_qaoa_is_reproducible() -> None:
    variable = ("A1", "I1")
    model = QuboModel(linear={variable: -1.0})
    solver = QiskitQAOASolver(shots=256, seed=7, maxiter=20)

    first = solver.solve(model)
    second = solver.solve(model)

    assert first == second


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"reps": 0}, "reps"),
        ({"shots": 0}, "shots"),
        ({"maxiter": 0}, "maxiter"),
    ],
)
def test_qaoa_rejects_invalid_configuration(kwargs: dict[str, int], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        QiskitQAOASolver(**kwargs)
