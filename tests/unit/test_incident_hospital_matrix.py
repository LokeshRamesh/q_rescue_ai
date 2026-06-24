from q_rescue.simulation.distance_matrix import build_incident_hospital_matrix
from q_rescue.simulation.generator import DisasterScenario
from q_rescue.domain.models import Hospital, Incident, Location, Severity, DisasterCategory


def test_incident_hospital_matrix_dimensions():
    scenario = DisasterScenario(
        name="test",
        ambulances=[],
        incidents=[
            Incident("I1", Location(0, 0), Severity.LOW),
            Incident("I2", Location(0, 0), Severity.LOW),
        ],
        hospitals=[
            Hospital("H1", "Test", Location(1, 1), 100, 50),
            Hospital("H2", "Test", Location(2, 2), 100, 50),
            Hospital("H3", "Test", Location(3, 3), 100, 50),
        ],
        category=DisasterCategory.GENERIC,
    )

    matrix = build_incident_hospital_matrix(scenario)
    assert len(matrix.incident_ids) == 2
    assert len(matrix.hospital_ids) == 3
    assert matrix.incident_ids == ["I1", "I2"]
    assert matrix.hospital_ids == ["H1", "H2", "H3"]
    assert len(matrix.matrix) == 2
    assert len(matrix.matrix["I1"]) == 3


def test_incident_hospital_matrix_custom_distance():
    scenario = DisasterScenario(
        name="test",
        ambulances=[],
        incidents=[
            Incident("I1", Location(0, 0), Severity.LOW),
        ],
        hospitals=[
            Hospital("H1", "Test", Location(1, 1), 100, 50),
        ],
        category=DisasterCategory.GENERIC,
    )

    def dummy_dist(loc1, loc2):
        return 42.0

    matrix = build_incident_hospital_matrix(scenario, distance_fn=dummy_dist)
    assert matrix.matrix["I1"]["H1"] == 42.0
