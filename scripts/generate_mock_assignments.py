import json
from pathlib import Path
import random

_PROJECT_ROOT = Path(__file__).parent.parent


def generate_mock_assignments(scenario_path: Path, out_path: Path):
    with scenario_path.open("r", encoding="utf-8") as f:
        scenario = json.load(f)

    assignments = []
    # Make some random assignments
    # Shuffle incidents and ambulances to pair them up
    incidents = scenario.get("incidents", [])
    ambulances = scenario.get("ambulances", [])
    hospitals = scenario.get("hospitals", [])

    random.shuffle(incidents)
    random.shuffle(ambulances)

    for i in range(min(len(ambulances), len(incidents))):
        amb = ambulances[i]
        inc = incidents[i]
        hosp = random.choice(hospitals) if hospitals else None

        assignment = {
            "ambulance_id": amb["id"],
            "incident_id": inc["id"],
            "hospital_id": hosp["id"] if hosp else None,
            "distance": round(random.uniform(1.0, 15.0), 2),
        }
        assignments.append(assignment)

    output = {"scenario_id": scenario.get("name", "Unknown Scenario"), "assignments": assignments}

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)

    print(f"Generated mock assignments at: {out_path}")


if __name__ == "__main__":
    demo_scenario = _PROJECT_ROOT / "data" / "demo" / "scenario.json"
    demo_out = _PROJECT_ROOT / "data" / "demo" / "assignments.json"

    if demo_scenario.exists():
        generate_mock_assignments(demo_scenario, demo_out)
    else:
        print(f"Scenario not found at {demo_scenario}. Please run generate_demo.py first.")
