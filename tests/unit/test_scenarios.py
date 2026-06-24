import pytest

from q_rescue.domain.models import DisasterCategory, Severity
from q_rescue.simulation.scenarios import (
    generate_scenario_by_category,
    generate_generic_scenario,
    generate_flood_scenario,
    generate_industrial_scenario,
    generate_city_wide_scenario,
)
from q_rescue.simulation.sheffield import validate_coordinates


@pytest.fixture
def base_config():
    return {
        "simulation": {
            "ambulances": 3,
            "incidents": 10,
            "cluster_radius_km": 1.0,
        }
    }


def test_generic_scenario_entity_counts(base_config):
    scenario = generate_generic_scenario(base_config, seed=42)

    assert len(scenario.ambulances) == 3
    assert len(scenario.incidents) == 10
    assert scenario.category == DisasterCategory.GENERIC
    assert len(scenario.hospitals) == 4

    # All entities should have valid coordinates
    for incident in scenario.incidents:
        assert validate_coordinates(incident.location.x, incident.location.y)


def test_city_wide_scenario_doubles_incidents(base_config):
    scenario = generate_city_wide_scenario(base_config, seed=42)

    assert len(scenario.ambulances) == 3
    # Should double the incident count (10 * 2 = 20)
    assert len(scenario.incidents) == 20
    assert scenario.category == DisasterCategory.CITY_WIDE_EMERGENCY


def test_industrial_scenario_high_severity(base_config):
    # 100 incidents to get a good statistical sample
    config = {"simulation": {"ambulances": 3, "incidents": 100}}
    scenario = generate_industrial_scenario(config, seed=42)

    critical_count = sum(1 for i in scenario.incidents if i.severity == Severity.CRITICAL)
    high_count = sum(1 for i in scenario.incidents if i.severity == Severity.HIGH)

    # Should be heavily weighted towards Critical/High (~80% combined)
    assert (critical_count + high_count) > 60


def test_flood_scenario_reduces_hospital_capacity(base_config):
    scenario = generate_flood_scenario(base_config, seed=42)

    # Capacity is reduced by 30% (multiplier = 0.70)
    northern_general = next(h for h in scenario.hospitals if h.id == "H1")

    # Original beds: 850 * 0.70 = 595
    assert 580 <= northern_general.available_beds <= 600


def test_dispatcher_routes_correctly(base_config):
    scenario = generate_scenario_by_category(DisasterCategory.FLOOD, base_config, seed=42)
    assert scenario.category == DisasterCategory.FLOOD

    scenario = generate_scenario_by_category(
        DisasterCategory.INDUSTRIAL_ACCIDENT, base_config, seed=42
    )
    assert scenario.category == DisasterCategory.INDUSTRIAL_ACCIDENT


def test_deterministic_generation(base_config):
    s1 = generate_generic_scenario(base_config, seed=123)
    s2 = generate_generic_scenario(base_config, seed=123)

    for i in range(len(s1.incidents)):
        assert s1.incidents[i].location.x == s2.incidents[i].location.x
        assert s1.incidents[i].location.y == s2.incidents[i].location.y
        assert s1.incidents[i].severity == s2.incidents[i].severity
