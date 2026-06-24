from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, Enum
from math import hypot, radians, sin, cos, asin, sqrt


class Severity(IntEnum):
    """Incident severity levels used across the simulation and QUBO model.

    QUBO formulation uses these integer values scaled by ``severity_weight``
    (default 8.0), which maps approximately to the spec's absolute weights:
        LOW(1)      × 8 =  8   ≈ spec Low=25      (order preserved)
        MEDIUM(2)   × 8 = 16   ≈ spec Medium=50
        HIGH(3)     × 8 = 24   ≈ spec High=75
        CRITICAL(4) × 8 = 32   ≈ spec Critical=100

    The absolute spec weights (25/50/75/100) are exposed in
    ``Severity.absolute_weight()`` for use in CSV exports and documentation.
    """

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def absolute_weight(self) -> int:
        """Return the spec-defined priority weight for reporting purposes."""
        return {
            Severity.LOW: 25,
            Severity.MEDIUM: 50,
            Severity.HIGH: 75,
            Severity.CRITICAL: 100,
        }[self]


class DisasterCategory(Enum):
    """Category of disaster scenario being simulated."""

    GENERIC = "generic"
    FLOOD = "flood"
    INDUSTRIAL_ACCIDENT = "industrial_accident"
    CITY_WIDE_EMERGENCY = "city_wide_emergency"


@dataclass(frozen=True)
class Location:
    """A geographic point that can represent either grid (km) or lat/lon coordinates.

    For Sheffield simulations, ``x`` holds latitude and ``y`` holds longitude.
    Use ``haversine_to()`` for accurate km distances between lat/lon coordinates
    and ``distance_to()`` for fast Euclidean distance on grid-based scenarios.
    """

    x: float  # latitude (geographic) or km east from origin (grid)
    y: float  # longitude (geographic) or km north from origin (grid)

    def distance_to(self, other: "Location") -> float:
        """Euclidean distance — accurate for grid/km coordinates."""
        return hypot(self.x - other.x, self.y - other.y)

    def haversine_to(self, other: "Location") -> float:
        """Great-circle (Haversine) distance in km for lat/lon coordinates."""
        lat1, lon1 = radians(self.x), radians(self.y)
        lat2, lon2 = radians(other.x), radians(other.y)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return 6371.0 * 2 * asin(sqrt(a))  # Earth radius = 6371 km


@dataclass(frozen=True)
class Ambulance:
    id: str
    location: Location
    status: str = "Available"


@dataclass(frozen=True)
class Hospital:
    """A Sheffield hospital with real capacity data."""

    id: str
    name: str
    location: Location
    capacity: int  # total licensed bed count
    available_beds: int  # beds available at simulation start


@dataclass(frozen=True)
class Incident:
    id: str
    location: Location
    severity: Severity
    category: DisasterCategory = DisasterCategory.GENERIC


@dataclass(frozen=True)
class Assignment:
    ambulance_id: str
    incident_id: str
    distance: float
    hospital_id: str | None = None


@dataclass
class OptimizationResult:
    assignments: list[Assignment]
    objective_value: float
    solver_name: str
    feasible: bool = True
    metadata: dict[str, object] = field(default_factory=dict)
