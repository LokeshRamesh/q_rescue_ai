import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from q_rescue.simulation.road_network import SheffieldRoadNetwork
from q_rescue.simulation.sheffield import SHEFFIELD_HOSPITALS
from q_rescue.domain.models import Location
from q_rescue.simulation.sheffield import haversine_distance


def main():
    print("Testing Sheffield Road Network (OSMnx)...")
    network = SheffieldRoadNetwork()

    print("Loading graph (this will download ~50MB on first run)...")
    try:
        network.load()
    except ImportError:
        print("osmnx is not installed. Run: pip install osmnx networkx")
        return

    print("Graph loaded successfully!\n")

    # Test a few hospital to incident routes
    test_incident = Location(53.3883, -1.4690)  # Don Valley flood zone

    print(f"{'Hospital':<30} | {'Haversine (km)':<15} | {'Road (km)':<15}")
    print("-" * 65)

    for hospital in SHEFFIELD_HOSPITALS:
        hav_dist = haversine_distance(hospital.location, test_incident)
        road_dist = network.shortest_path_distance(hospital.location, test_incident)

        print(f"{hospital.name:<30} | {hav_dist:<15.2f} | {road_dist:<15.2f}")

    print("\nSpike complete.")


if __name__ == "__main__":
    main()
