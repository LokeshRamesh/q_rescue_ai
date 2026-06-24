import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from q_rescue.domain.models import DisasterCategory
from q_rescue.simulation.distance_matrix import (
    build_distance_matrix,
    build_severity_mapping,
    build_incident_hospital_matrix,
)
from q_rescue.simulation.exporters import export_all
from q_rescue.simulation.scenarios import generate_scenario_by_category
from q_rescue.simulation.constraints import OperationalConstraints


def generate_benchmark(name: str, ambulances: int, incidents: int, category: DisasterCategory):
    print(f"Generating benchmark '{name}' ({ambulances} ambulances, {incidents} incidents)...")

    # Mock config for the generator
    config = {
        "simulation": {
            "ambulances": ambulances,
            "incidents": incidents,
            "category": category.value,
            "cluster_radius_km": 1.0,
            "use_sheffield_coords": True,
        }
    }

    scenario = generate_scenario_by_category(category, config, seed=42)
    distance_matrix = build_distance_matrix(scenario)
    incident_hospital_matrix = build_incident_hospital_matrix(scenario)
    severity_mapping = build_severity_mapping(scenario)
    constraints = OperationalConstraints.from_config(config)

    out_dir = _PROJECT_ROOT / "data" / "benchmarks" / name
    export_all(
        scenario,
        distance_matrix,
        severity_mapping,
        out_dir,
        incident_hospital_matrix=incident_hospital_matrix,
        constraints=constraints,
    )
    print(f"Saved {name} benchmark to {out_dir}")


def main():
    generate_benchmark("small", 3, 5, DisasterCategory.FLOOD)
    generate_benchmark("medium", 10, 20, DisasterCategory.FLOOD)
    generate_benchmark("large", 20, 50, DisasterCategory.CITY_WIDE_EMERGENCY)
    print("Done.")


if __name__ == "__main__":
    main()
