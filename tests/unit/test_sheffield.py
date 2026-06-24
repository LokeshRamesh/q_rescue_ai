from random import Random
import math

from q_rescue.domain.models import Location
from q_rescue.simulation.sheffield import (
    validate_coordinates,
    random_sheffield_location,
    haversine_distance,
    clustered_location,
    SHEFFIELD_BOUNDS,
    SHEFFIELD_HOSPITALS,
)


def test_validate_coordinates_inside_bounds():
    # Inside Sheffield bounds
    assert validate_coordinates(53.38, -1.47) is True


def test_validate_coordinates_outside_bounds():
    # Outside Sheffield bounds (London)
    assert validate_coordinates(51.5, -0.1) is False


def test_random_sheffield_location_returns_valid_coords():
    rng = Random(42)
    for _ in range(100):
        loc = random_sheffield_location(rng)
        assert validate_coordinates(loc.x, loc.y) is True


def test_clustered_location_stays_within_bounds():
    rng = Random(42)
    # Use a centroid near the edge of the bounding box
    edge_centroid = Location(SHEFFIELD_BOUNDS["lat_min"], SHEFFIELD_BOUNDS["lon_min"])

    for _ in range(50):
        # Large radius to force spread
        loc = clustered_location(rng, edge_centroid, radius_km=10.0)
        assert validate_coordinates(loc.x, loc.y) is True


def test_haversine_distance_between_hospitals():
    # Northern General (H1) and Royal Hallamshire (H2)
    h1_loc = SHEFFIELD_HOSPITALS[0].location
    h2_loc = SHEFFIELD_HOSPITALS[1].location

    distance = haversine_distance(h1_loc, h2_loc)

    # Distance should be approximately 4-5 km
    assert 3.5 <= distance <= 5.5


def test_haversine_distance_zero_for_same_point():
    loc = Location(53.38, -1.47)
    assert math.isclose(haversine_distance(loc, loc), 0.0, abs_tol=1e-5)
