import numpy as np
import pandas as pd

from q_rescue.domain.models import Severity
from q_rescue.simulation.distance_matrix import build_distance_matrix, build_severity_mapping
from q_rescue.simulation.scenarios import generate_generic_scenario
from dataclasses import replace


def test_distance_matrix_dimensions():
    scenario = generate_generic_scenario(config={"simulation": {"ambulances": 3, "incidents": 5}})
    dm = build_distance_matrix(scenario)

    assert len(dm.matrix) == 3
    for a_id in dm.matrix:
        assert len(dm.matrix[a_id]) == 5
        for i_id in dm.matrix[a_id]:
            # Haversine distance should be > 0 but relatively small in a city
            assert 0.0 <= dm.matrix[a_id][i_id] < 100.0


def test_severity_mapping_extracts_absolute_weights():
    scenario = generate_generic_scenario(config={"simulation": {"ambulances": 1, "incidents": 4}})

    # Force the 4 incidents to cover all 4 severities (incidents are frozen dataclasses)
    scenario.incidents[0] = replace(scenario.incidents[0], severity=Severity.LOW)
    scenario.incidents[1] = replace(scenario.incidents[1], severity=Severity.MEDIUM)
    scenario.incidents[2] = replace(scenario.incidents[2], severity=Severity.HIGH)
    scenario.incidents[3] = replace(scenario.incidents[3], severity=Severity.CRITICAL)

    mapping = build_severity_mapping(scenario)

    assert mapping[scenario.incidents[0].id] == 25
    assert mapping[scenario.incidents[1].id] == 50
    assert mapping[scenario.incidents[2].id] == 75
    assert mapping[scenario.incidents[3].id] == 100


def test_to_dataframe():
    scenario = generate_generic_scenario(config={"simulation": {"ambulances": 2, "incidents": 3}})
    dm = build_distance_matrix(scenario)
    df = dm.to_dataframe()

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 3)
    assert list(df.index) == [a.id for a in scenario.ambulances]
    assert list(df.columns) == [i.id for i in scenario.incidents]


def test_to_numpy():
    scenario = generate_generic_scenario(config={"simulation": {"ambulances": 2, "incidents": 3}})
    dm = build_distance_matrix(scenario)
    arr = dm.to_numpy()

    assert isinstance(arr, np.ndarray)
    assert arr.shape == (2, 3)
