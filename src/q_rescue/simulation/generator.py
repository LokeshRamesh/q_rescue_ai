"""Updated DisasterScenario generator for the Q-Rescue shared package.

The ``generate_scenario`` function is the primary entry-point used by:
- ``scripts/run_poc.py``
- ``app/streamlit_app.py``
- ``src/q_rescue/services/response_service.py``

It is backwards-compatible: existing callers that do not pass ``category``
or ``hospitals`` continue to work unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

from q_rescue.domain.models import (
    Ambulance,
    DisasterCategory,
    Hospital,
    Incident,
    Location,
    Severity,
)
from q_rescue.simulation.sheffield import (
    SHEFFIELD_HOSPITALS,
    random_sheffield_location,
)


@dataclass(frozen=True)
class DisasterScenario:
    """An immutable snapshot of a simulated Sheffield emergency.

    Attributes:
        name:       Human-readable scenario label.
        ambulances: Available ambulances at the start of the period.
        incidents:  Active incidents requiring a response.
        hospitals:  Sheffield hospitals with current capacity data.
        category:   The disaster type used to generate this scenario.
    """

    name: str
    ambulances: list[Ambulance]
    incidents: list[Incident]
    hospitals: list[Hospital]
    category: DisasterCategory = DisasterCategory.GENERIC


def generate_scenario(
    ambulance_count: int = 3,
    incident_count: int = 5,
    map_width_km: float = 20.0,
    seed: int = 42,
    category: DisasterCategory = DisasterCategory.GENERIC,
    use_sheffield_coords: bool = True,
) -> DisasterScenario:
    """Create a deterministic synthetic scenario.

    Backwards-compatible with the original Week 1 POC signature.
    When ``use_sheffield_coords=True`` (default), incidents and ambulances
    are placed using real Sheffield lat/lon coordinates. Otherwise the legacy
    grid-based placement (0..map_width_km) is used.

    Args:
        ambulance_count:      Number of ambulances to generate.
        incident_count:       Number of incidents to generate.
        map_width_km:         Grid size when not using Sheffield coords.
        seed:                 Random seed for reproducibility.
        category:             Disaster category tag on each incident.
        use_sheffield_coords: Use lat/lon placement inside Sheffield bounds.

    Returns:
        A fully populated ``DisasterScenario``.
    """
    rng = Random(seed)

    if use_sheffield_coords:
        ambulances = [
            Ambulance(
                id=f"A{i + 1}",
                location=random_sheffield_location(rng),
            )
            for i in range(ambulance_count)
        ]
        incidents = [
            Incident(
                id=f"I{i + 1}",
                location=random_sheffield_location(rng),
                severity=Severity(rng.randint(1, 4)),
                category=category,
            )
            for i in range(incident_count)
        ]
    else:
        # Legacy grid-based placement (km coordinates)
        ambulances = [
            Ambulance(
                id=f"A{i + 1}",
                location=Location(
                    rng.uniform(0, map_width_km),
                    rng.uniform(0, map_width_km),
                ),
            )
            for i in range(ambulance_count)
        ]
        incidents = [
            Incident(
                id=f"I{i + 1}",
                location=Location(
                    rng.uniform(0, map_width_km),
                    rng.uniform(0, map_width_km),
                ),
                severity=Severity(rng.randint(1, 4)),
                category=category,
            )
            for i in range(incident_count)
        ]

    return DisasterScenario(
        name="Synthetic flood response POC",
        ambulances=ambulances,
        incidents=incidents,
        hospitals=list(SHEFFIELD_HOSPITALS),
        category=category,
    )
