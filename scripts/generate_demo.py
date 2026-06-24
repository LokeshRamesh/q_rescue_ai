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


def main():
    print("Generating Demo Scenario (Sheffield Flood Response)...")

    # Override config for the demo scenario
    config = {
        "simulation": {
            "ambulances": 10,
            "incidents": 20,
            "category": "flood",
            "cluster_radius_km": 1.0,  # Clustered around Don valley
            "use_sheffield_coords": True,
        }
    }

    # Generate the scenario
    # We use seed=42 to make it deterministic
    scenario = generate_scenario_by_category(DisasterCategory.FLOOD, config, seed=42)

    # Manually reduce hospital capacity to 50% for the demo
    from q_rescue.domain.models import Hospital

    new_hospitals = []
    for h in scenario.hospitals:
        new_hospitals.append(
            Hospital(
                id=h.id,
                name=h.name,
                location=h.location,
                capacity=h.capacity,
                available_beds=int(h.capacity * 0.5),
            )
        )
    # Replace hospitals tuple/list with new one (using object.__setattr__ since DisasterScenario is frozen)
    object.__setattr__(scenario, "hospitals", new_hospitals)

    distance_matrix = build_distance_matrix(scenario)
    incident_hospital_matrix = build_incident_hospital_matrix(scenario)
    severity_mapping = build_severity_mapping(scenario)
    constraints = OperationalConstraints.from_config(config)

    out_dir = _PROJECT_ROOT / "data" / "demo"
    export_all(
        scenario,
        distance_matrix,
        severity_mapping,
        out_dir,
        incident_hospital_matrix=incident_hospital_matrix,
        constraints=constraints,
    )
    print(f"Saved Demo Dataset v1 to {out_dir}")
    print("Done.")


if __name__ == "__main__":
    main()
