"""Sheffield geographic model for the Q-Rescue AI simulation.

Provides:
- Sheffield bounding-box constants (WGS-84 lat/lon)
- Real hospital locations with capacity data
- Known flood and industrial disaster zones
- Utility functions for coordinate generation and validation
- Haversine distance calculation
"""

from __future__ import annotations

import math
from random import Random
from typing import TYPE_CHECKING

from q_rescue.domain.models import Hospital, Location

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Sheffield geographic bounding box (WGS-84)
# ---------------------------------------------------------------------------
SHEFFIELD_BOUNDS: dict[str, float] = {
    "lat_min": 53.3000,
    "lat_max": 53.4500,
    "lon_min": -1.5500,
    "lon_max": -1.3500,
}

# ---------------------------------------------------------------------------
# Real Sheffield hospitals with approximate capacity data
# ---------------------------------------------------------------------------
SHEFFIELD_HOSPITALS: list[Hospital] = [
    Hospital(
        id="H1",
        name="Northern General Hospital",
        location=Location(53.4096, -1.4565),
        capacity=1100,
        available_beds=850,
    ),
    Hospital(
        id="H2",
        name="Royal Hallamshire Hospital",
        location=Location(53.3782, -1.4883),
        capacity=900,
        available_beds=680,
    ),
    Hospital(
        id="H3",
        name="Sheffield Children's Hospital",
        location=Location(53.3728, -1.4908),
        capacity=200,
        available_beds=150,
    ),
    Hospital(
        id="H4",
        name="Weston Park Hospital",
        location=Location(53.3778, -1.4943),
        capacity=72,
        available_beds=55,
    ),
]

# ---------------------------------------------------------------------------
# Known Sheffield disaster zones (cluster centroids)
# ---------------------------------------------------------------------------

# Flood-risk zones along the Don and Sheaf river valleys
FLOOD_ZONES: list[Location] = [
    Location(53.3883, -1.4690),  # Don Valley (Meadowhall area)
    Location(53.3600, -1.4700),  # Sheaf Valley (city centre south)
    Location(53.4100, -1.4200),  # Blackburn Meadows (lower Don)
]

# Industrial/chemical incident zones
INDUSTRIAL_ZONES: list[Location] = [
    Location(53.3950, -1.4100),  # Tinsley industrial estate
    Location(53.3750, -1.4150),  # Attercliffe corridor
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_coordinates(lat: float, lon: float) -> bool:
    """Return True if the coordinates fall within Sheffield's bounding box."""
    return (
        SHEFFIELD_BOUNDS["lat_min"] <= lat <= SHEFFIELD_BOUNDS["lat_max"]
        and SHEFFIELD_BOUNDS["lon_min"] <= lon <= SHEFFIELD_BOUNDS["lon_max"]
    )


def random_sheffield_location(
    rng: Random,
    bounds: dict[str, float] | None = None,
) -> Location:
    """Generate a uniformly random ``Location`` within Sheffield (or custom bounds).

    Args:
        rng: A seeded ``random.Random`` instance for reproducibility.
        bounds: Optional override for the geographic bounds dict.
                Must contain ``lat_min``, ``lat_max``, ``lon_min``, ``lon_max``.

    Returns:
        A ``Location`` with valid Sheffield lat/lon coordinates.
    """
    b = bounds or SHEFFIELD_BOUNDS
    lat = rng.uniform(b["lat_min"], b["lat_max"])
    lon = rng.uniform(b["lon_min"], b["lon_max"])
    return Location(lat, lon)


def clustered_location(
    rng: Random,
    centroid: Location,
    radius_km: float = 1.0,
) -> Location:
    """Generate a random ``Location`` near a centroid using Gaussian spread.

    Samples are clipped to Sheffield bounds to avoid out-of-area coordinates.

    Args:
        rng: A seeded ``random.Random`` instance.
        centroid: The cluster centre (lat/lon).
        radius_km: 1-sigma spread in km. ~68% of points fall within this radius.

    Returns:
        A ``Location`` near the centroid, clamped to Sheffield bounds.
    """
    # 1 degree latitude ≈ 111.32 km; 1 degree longitude ≈ 111.32 × cos(lat) km
    lat_sigma = radius_km / 111.32
    lon_sigma = radius_km / (111.32 * math.cos(math.radians(centroid.x)))

    lat = rng.gauss(centroid.x, lat_sigma)
    lon = rng.gauss(centroid.y, lon_sigma)

    # Clamp to Sheffield bounds
    lat = max(SHEFFIELD_BOUNDS["lat_min"], min(SHEFFIELD_BOUNDS["lat_max"], lat))
    lon = max(SHEFFIELD_BOUNDS["lon_min"], min(SHEFFIELD_BOUNDS["lon_max"], lon))

    return Location(lat, lon)


def haversine_distance(loc1: Location, loc2: Location) -> float:
    """Compute the great-circle distance in km between two lat/lon locations.

    This is the standalone module-level function. The same logic is available
    as ``Location.haversine_to()`` on the domain model.
    """
    return loc1.haversine_to(loc2)


def nearest_hospital(location: Location, hospitals: list[Hospital]) -> Hospital:
    """Return the hospital closest (Haversine) to the given location."""
    return min(hospitals, key=lambda h: haversine_distance(location, h.location))
