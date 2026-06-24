from copy import deepcopy

import pytest

pytest.importorskip("qiskit_optimization")

from q_rescue.domain.models import Ambulance, Incident, Location, Severity
from q_rescue.quantum.qiskit_adapter import to_quadratic_program
from q_rescue.quantum.qubo import AmbulanceAllocationQuboBuilder
from q_rescue.simulation.distance_matrix import build_distance_matrix, build_severity_mapping
from q_rescue.simulation.generator import DisasterScenario


def _build_small_qubo():
    ambulances = [
        Ambulance("A1", Location(0.0, 0.0)),
        Ambulance("A2", Location(0.003, 0.0)),
    ]
    incidents = [
        Incident("I1", Location(0.001, 0.0), Severity.CRITICAL),
        Incident("I2", Location(0.004, 0.0), Severity.LOW),
    ]
    scenario = DisasterScenario(
        name="test", ambulances=ambulances, incidents=incidents, hospitals=[]
    )
    dm = build_distance_matrix(scenario)
    sm = build_severity_mapping(scenario)
    return AmbulanceAllocationQuboBuilder().build(ambulances, incidents, dm, sm)


def test_conversion_creates_binary_variables_and_reversible_mappings() -> None:
    model = _build_small_qubo()

    conversion = to_quadratic_program(model)

    assert conversion.program.get_num_binary_vars() == len(model.variables)
    assert len(conversion.variable_to_name) == len(model.variables)
    for variable, name in conversion.variable_to_name.items():
        assert conversion.name_to_variable[name] == variable


@pytest.mark.parametrize(
    "bits",
    [
        (0, 0, 0, 0),
        (1, 0, 0, 1),
        (0, 1, 1, 0),
        (1, 1, 0, 0),
    ],
)
def test_qiskit_objective_matches_framework_neutral_qubo(bits: tuple[int, ...]) -> None:
    model = _build_small_qubo()
    conversion = to_quadratic_program(model)
    tuple_sample = dict(zip(model.variables, bits, strict=True))

    qiskit_value = conversion.program.objective.evaluate(list(bits))

    assert qiskit_value == pytest.approx(model.evaluate(tuple_sample))


def test_conversion_does_not_mutate_original_qubo() -> None:
    model = _build_small_qubo()
    original = deepcopy(model)

    to_quadratic_program(model)

    assert model == original


def test_qiskit_sample_can_be_decoded_to_domain_variables() -> None:
    model = _build_small_qubo()
    conversion = to_quadratic_program(model)
    named_sample = {
        conversion.variable_to_name[variable]: index % 2
        for index, variable in enumerate(model.variables)
    }

    decoded = conversion.decode_sample(named_sample)

    assert decoded == {variable: index % 2 for index, variable in enumerate(model.variables)}
