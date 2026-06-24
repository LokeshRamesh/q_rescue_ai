"""Raw ambulance-to-incident distance matrix for the Q-Rescue optimisation problem.

This module replaces the old ``cost_matrix.py``. Per the schema specification,
the simulation engine is responsible for generating raw distance data only.
Objective function construction (weighting distances against severity) is the
responsibility of the solver modules (Member 1 & Member 4).

Schema output:
    distance_matrix.json / distance_matrix.csv  –  raw distances in km
    severity_weights.json / severity_weights.csv  –  {incident_id: weight}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from q_rescue.domain.models import Location, Severity
from q_rescue.simulation.generator import DisasterScenario
from q_rescue.simulation.sheffield import haversine_distance

# Absolute severity weights per schema specification §4
# LOW=25, MEDIUM=50, HIGH=75, CRITICAL=100
SEVERITY_WEIGHTS: dict[Severity, int] = {
    Severity.LOW: 25,
    Severity.MEDIUM: 50,
    Severity.HIGH: 75,
    Severity.CRITICAL: 100,
}


@dataclass
class DistanceMatrix:
    """Raw ambulance-to-incident travel distances in kilometres.

    Attributes:
        matrix:        Nested dict ``{ambulance_id: {incident_id: distance_km}}``.
        ambulance_ids: Ordered list of ambulance IDs (row index).
        incident_ids:  Ordered list of incident IDs (column index).
    """

    matrix: dict[str, dict[str, float]] = field(default_factory=dict)
    ambulance_ids: list[str] = field(default_factory=list)
    incident_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, dict[str, float]]:
        """Return the distance matrix as a plain nested dict (JSON-serialisable)."""
        return self.matrix

    def to_dataframe(self):  # -> pd.DataFrame
        """Return the distance matrix as a pandas DataFrame (rows=ambulances, cols=incidents)."""
        import pandas as pd  # noqa: PLC0415

        return pd.DataFrame(self.matrix).T.reindex(
            index=self.ambulance_ids, columns=self.incident_ids
        )

    def to_numpy(self):
        """Return distance values as a 2-D NumPy array (rows=ambulances, cols=incidents)."""
        import numpy as np  # noqa: PLC0415

        return np.array(
            [
                [self.matrix[a_id][i_id] for i_id in self.incident_ids]
                for a_id in self.ambulance_ids
            ],
            dtype=float,
        )


@dataclass
class IncidentHospitalMatrix:
    """Raw incident-to-hospital travel distances in kilometres.

    Attributes:
        matrix:       Nested dict ``{incident_id: {hospital_id: distance_km}}``.
        incident_ids: Ordered list of incident IDs (row index).
        hospital_ids: Ordered list of hospital IDs (column index).
    """

    matrix: dict[str, dict[str, float]] = field(default_factory=dict)
    incident_ids: list[str] = field(default_factory=list)
    hospital_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, dict[str, float]]:
        """Return the distance matrix as a plain nested dict (JSON-serialisable)."""
        return self.matrix

    def to_dataframe(self):
        """Return the distance matrix as a pandas DataFrame (rows=incidents, cols=hospitals)."""
        import pandas as pd  # noqa: PLC0415

        return pd.DataFrame(self.matrix).T.reindex(
            index=self.incident_ids, columns=self.hospital_ids
        )

    def to_numpy(self):
        """Return distance values as a 2-D NumPy array (rows=incidents, cols=hospitals)."""
        import numpy as np  # noqa: PLC0415

        return np.array(
            [[self.matrix[i_id][h_id] for h_id in self.hospital_ids] for i_id in self.incident_ids],
            dtype=float,
        )


# Type alias for the severity mapping
SeverityMapping = dict[str, int]  # {incident_id: weight (25/50/75/100)}


def build_distance_matrix(
    scenario: DisasterScenario,
    distance_fn: Callable[[Location, Location], float] | None = None,
) -> DistanceMatrix:
    """Build a raw ambulance-to-incident distance matrix from a scenario.

    Args:
        scenario:    A ``DisasterScenario`` produced by any generator.
        distance_fn: Optional custom distance function
                     ``(Location, Location) -> float`` returning km.
                     Defaults to Haversine (great-circle) distance.

    Returns:
        A populated ``DistanceMatrix`` instance containing raw distances only.

    Example::

        from q_rescue.simulation.distance_matrix import build_distance_matrix, build_severity_mapping

        dm = build_distance_matrix(scenario)
        sm = build_severity_mapping(scenario)

        # Pass both to the solvers:
        qubo_model = builder.build(scenario.ambulances, scenario.incidents, dm, sm)
    """
    dist = distance_fn if distance_fn is not None else _haversine

    ambulance_ids = [a.id for a in scenario.ambulances]
    incident_ids = [i.id for i in scenario.incidents]

    matrix: dict[str, dict[str, float]] = {}

    for ambulance in scenario.ambulances:
        matrix[ambulance.id] = {}
        for incident in scenario.incidents:
            d = dist(ambulance.location, incident.location)
            matrix[ambulance.id][incident.id] = round(d, 6)

    return DistanceMatrix(
        matrix=matrix,
        ambulance_ids=ambulance_ids,
        incident_ids=incident_ids,
    )


def build_incident_hospital_matrix(
    scenario: DisasterScenario,
    distance_fn: Callable[[Location, Location], float] | None = None,
) -> IncidentHospitalMatrix:
    """Build a raw incident-to-hospital distance matrix from a scenario.

    Args:
        scenario:    A ``DisasterScenario`` produced by any generator.
        distance_fn: Optional custom distance function
                     ``(Location, Location) -> float`` returning km.
                     Defaults to Haversine (great-circle) distance.

    Returns:
        A populated ``IncidentHospitalMatrix`` instance containing raw distances only.
    """
    dist = distance_fn if distance_fn is not None else _haversine

    incident_ids = [i.id for i in scenario.incidents]
    hospital_ids = [h.id for h in scenario.hospitals]

    matrix: dict[str, dict[str, float]] = {}

    for incident in scenario.incidents:
        matrix[incident.id] = {}
        for hospital in scenario.hospitals:
            d = dist(incident.location, hospital.location)
            matrix[incident.id][hospital.id] = round(d, 6)

    return IncidentHospitalMatrix(
        matrix=matrix,
        incident_ids=incident_ids,
        hospital_ids=hospital_ids,
    )


def build_severity_mapping(scenario: DisasterScenario) -> SeverityMapping:
    """Extract the absolute severity weight for each incident.

    Returns a flat dict ``{incident_id: weight}`` using the schema's
    absolute scale: LOW=25, MEDIUM=50, HIGH=75, CRITICAL=100.

    Args:
        scenario: A ``DisasterScenario`` produced by any generator.

    Returns:
        A ``SeverityMapping`` dict ready for export or solver consumption.

    Example::

        sm = build_severity_mapping(scenario)
        # {"I1": 25, "I2": 100, "I3": 75}
    """
    return {incident.id: SEVERITY_WEIGHTS[incident.severity] for incident in scenario.incidents}


def _haversine(loc1: Location, loc2: Location) -> float:
    """Default distance function: great-circle distance in km."""
    return haversine_distance(loc1, loc2)
