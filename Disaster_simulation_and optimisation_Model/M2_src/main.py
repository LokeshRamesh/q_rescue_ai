import tomllib
from pathlib import Path

from q_rescue.domain.models import DisasterCategory
from q_rescue.simulation.distance_matrix import build_distance_matrix, build_severity_mapping, build_incident_hospital_matrix
from q_rescue.simulation.exporters import export_all
from q_rescue.simulation.scenarios import generate_scenario_by_category
from q_rescue.simulation.constraints import OperationalConstraints

# Project root is three levels up: M2_src/ -> Disaster_simulation_.../ -> q_rescue_ai/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> None:
    # Load configuration
    config_path = _PROJECT_ROOT / "configs" / "default.toml"
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    # 1. Parse category
    category_str = config.get("simulation", {}).get("category", "generic")
    try:
        category = DisasterCategory(category_str)
    except ValueError:
        print(f"Warning: Unknown category '{category_str}', falling back to GENERIC.")
        category = DisasterCategory.GENERIC

    seed = int(config.get("simulation", {}).get("seed", 42))


    # 2. Generate scenario
    print(f"Generating {category.value} scenario (seed={seed})...")
    scenario = generate_scenario_by_category(category, config, seed=seed)
    print(f"Generated {len(scenario.ambulances)} ambulances, "
          f"{len(scenario.incidents)} incidents.")

    print("Building raw distance matrix (Haversine)...")
    distance_matrix = build_distance_matrix(scenario)
    
    print("Building incident->hospital matrix...")
    incident_hospital_matrix = build_incident_hospital_matrix(scenario)
    
    print("Extracting severity mapping...")
    severity_mapping = build_severity_mapping(scenario)
    
    print("Loading constraints...")
    constraints = OperationalConstraints.from_config(config)

    # 4. Export Outputs
    export_config = config.get("export", {})
    out_dir_str = str(export_config.get("export_dir", "data/outputs"))
    formats = list(export_config.get("formats", ["json", "csv"]))

    out_dir = _PROJECT_ROOT / out_dir_str
    print(f"Exporting data to {out_dir}...")

    generated = export_all(
        scenario, 
        distance_matrix, 
        severity_mapping, 
        out_dir, 
        incident_hospital_matrix=incident_hospital_matrix,
        constraints=constraints,
        formats=formats
    )
    for name, path in generated.items():
        print(f"  - {name}: {path.relative_to(_PROJECT_ROOT)}")

    print("Done.")


if __name__ == "__main__":
    main()
