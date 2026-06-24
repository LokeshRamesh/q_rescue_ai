"""Export module for simulation scenarios, distance matrices, and severity mappings.

Provides functions to serialise ``DisasterScenario``, ``DistanceMatrix``, and
``SeverityMapping`` to JSON and CSV formats per the Member 2 Output Schema Specification.

Per the schema:
    - scenario.json       – full scenario (ambulances, incidents, hospitals)
    - distance_matrix.json / .csv  – raw ambulance-to-incident distances (km)
    - severity_weights.json / .csv – per-incident absolute severity weights (25/50/75/100)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from q_rescue.simulation.distance_matrix import (
    DistanceMatrix,
    SeverityMapping,
    IncidentHospitalMatrix,
)
from q_rescue.simulation.generator import DisasterScenario
from q_rescue.simulation.constraints import OperationalConstraints


# ---------------------------------------------------------------------------
# JSON Exporters
# ---------------------------------------------------------------------------


def export_scenario_json(scenario: DisasterScenario, path: Path) -> None:
    """Export the entire scenario to a single JSON file."""
    data = {
        "scenario_id": scenario.name.lower().replace(" ", "_"),
        "name": scenario.name,
        "category": scenario.category.value,
        "ambulances": [
            {
                "id": a.id,
                "lat": round(a.location.x, 6),
                "lon": round(a.location.y, 6),
                "status": "available",
            }
            for a in scenario.ambulances
        ],
        "incidents": [
            {
                "id": i.id,
                "lat": round(i.location.x, 6),
                "lon": round(i.location.y, 6),
                "severity_level": i.severity.name,
                "severity_weight": i.severity.absolute_weight(),
            }
            for i in scenario.incidents
        ],
        "hospitals": [
            {
                "id": h.id,
                "name": h.name,
                "lat": round(h.location.x, 6),
                "lon": round(h.location.y, 6),
                "capacity": h.capacity,
                "available_beds": h.available_beds,
            }
            for h in scenario.hospitals
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def export_distance_matrix_json(distance_matrix: DistanceMatrix, path: Path) -> None:
    """Export the raw distance matrix to JSON.

    Format: {"A1": {"I1": 2.61, "I2": 10.85, ...}, ...}
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(distance_matrix.to_dict(), f, indent=4)


def export_severity_weights_json(severity_mapping: SeverityMapping, path: Path) -> None:
    """Export per-incident severity weights to JSON.

    Format: {"I1": 25, "I2": 100, "I3": 75}
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(severity_mapping, f, indent=4)


def export_incident_hospital_matrix_json(matrix: IncidentHospitalMatrix, path: Path) -> None:
    """Export the raw incident-to-hospital distance matrix to JSON.

    Format: {"I1": {"H1": 3.2, "H2": 7.8}, ...}
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(matrix.to_dict(), f, indent=4)


def export_constraints_json(constraints: OperationalConstraints, path: Path) -> None:
    """Export the operational constraints to JSON.

    Format: {"one_ambulance_per_incident": true, ...}
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(constraints.to_dict(), f, indent=4)


# ---------------------------------------------------------------------------
# CSV Exporters
# ---------------------------------------------------------------------------


def export_scenario_csv(scenario: DisasterScenario, output_dir: Path) -> None:
    """Export the scenario into separate CSV files (ambulances, incidents, hospitals)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    _write_csv(
        output_dir / "ambulances.csv",
        headers=["id", "lat", "lon", "status"],
        rows=[
            [a.id, round(a.location.x, 6), round(a.location.y, 6), "available"]
            for a in scenario.ambulances
        ],
    )

    _write_csv(
        output_dir / "incidents.csv",
        headers=["id", "lat", "lon", "severity_level", "severity_weight", "category"],
        rows=[
            [
                i.id,
                round(i.location.x, 6),
                round(i.location.y, 6),
                i.severity.name,
                i.severity.absolute_weight(),
                i.category.value,
            ]
            for i in scenario.incidents
        ],
    )

    _write_csv(
        output_dir / "hospitals.csv",
        headers=["id", "name", "lat", "lon", "capacity", "available_beds"],
        rows=[
            [
                h.id,
                h.name,
                round(h.location.x, 6),
                round(h.location.y, 6),
                h.capacity,
                h.available_beds,
            ]
            for h in scenario.hospitals
        ],
    )


def export_distance_matrix_csv(distance_matrix: DistanceMatrix, path: Path) -> None:
    """Export the distance matrix to CSV (rows = ambulances, cols = incidents)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ambulance_id"] + distance_matrix.incident_ids)
        for a_id in distance_matrix.ambulance_ids:
            row = [a_id] + [
                distance_matrix.matrix[a_id][i_id] for i_id in distance_matrix.incident_ids
            ]
            writer.writerow(row)


def export_severity_weights_csv(severity_mapping: SeverityMapping, path: Path) -> None:
    """Export per-incident severity weights to CSV.

    Columns: incident_id, severity_weight
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["incident_id", "severity_weight"])
        for incident_id, weight in severity_mapping.items():
            writer.writerow([incident_id, weight])


def export_incident_hospital_matrix_csv(matrix: IncidentHospitalMatrix, path: Path) -> None:
    """Export the distance matrix to CSV (rows = incidents, cols = hospitals)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["incident_id"] + matrix.hospital_ids)
        for i_id in matrix.incident_ids:
            row = [i_id] + [matrix.matrix[i_id][h_id] for h_id in matrix.hospital_ids]
            writer.writerow(row)


def _write_csv(path: Path, headers: list[str], rows: list[list[Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# One-shot Export
# ---------------------------------------------------------------------------


def export_all(
    scenario: DisasterScenario,
    distance_matrix: DistanceMatrix,
    severity_mapping: SeverityMapping,
    output_dir: Path,
    incident_hospital_matrix: IncidentHospitalMatrix | None = None,
    constraints: OperationalConstraints | None = None,
    formats: list[str] | None = None,
) -> dict[str, Path]:
    """Generate all requested exports in a single call.

    Args:
        scenario:         The simulated scenario.
        distance_matrix:  The raw distance matrix.
        severity_mapping: Per-incident severity weights.
        output_dir:       Target directory for all output files.
        incident_hospital_matrix: Optional incident-to-hospital distance matrix.
        constraints:      Optional operational constraints.
        formats:          List containing "json", "csv", or both. Defaults to both.

    Returns:
        A dict mapping descriptive names to the generated file paths.
    """
    if formats is None:
        formats = ["json", "csv"]

    output_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, Path] = {}

    if "json" in formats:
        p_scen = output_dir / "scenario.json"
        p_dist = output_dir / "distance_matrix.json"
        p_sev = output_dir / "severity_weights.json"
        export_scenario_json(scenario, p_scen)
        export_distance_matrix_json(distance_matrix, p_dist)
        export_severity_weights_json(severity_mapping, p_sev)
        generated["scenario_json"] = p_scen
        generated["distance_matrix_json"] = p_dist
        generated["severity_weights_json"] = p_sev

        if incident_hospital_matrix:
            p_ih = output_dir / "incident_hospital_matrix.json"
            export_incident_hospital_matrix_json(incident_hospital_matrix, p_ih)
            generated["incident_hospital_matrix_json"] = p_ih

        if constraints:
            p_cons = output_dir / "constraints.json"
            export_constraints_json(constraints, p_cons)
            generated["constraints_json"] = p_cons

    if "csv" in formats:
        export_scenario_csv(scenario, output_dir)
        p_dist_csv = output_dir / "distance_matrix.csv"
        p_sev_csv = output_dir / "severity_weights.csv"
        export_distance_matrix_csv(distance_matrix, p_dist_csv)
        export_severity_weights_csv(severity_mapping, p_sev_csv)
        generated["ambulances_csv"] = output_dir / "ambulances.csv"
        generated["incidents_csv"] = output_dir / "incidents.csv"
        generated["hospitals_csv"] = output_dir / "hospitals.csv"
        generated["distance_matrix_csv"] = p_dist_csv
        generated["severity_weights_csv"] = p_sev_csv

        if incident_hospital_matrix:
            p_ih_csv = output_dir / "incident_hospital_matrix.csv"
            export_incident_hospital_matrix_csv(incident_hospital_matrix, p_ih_csv)
            generated["incident_hospital_matrix_csv"] = p_ih_csv

    return generated
