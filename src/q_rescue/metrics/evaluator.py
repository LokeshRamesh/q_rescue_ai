from q_rescue.domain.models import Incident, OptimizationResult, Severity


def calculate_metrics(result: OptimizationResult, incidents: list[Incident]) -> dict[str, float]:
    assigned_ids = {item.incident_id for item in result.assignments}
    critical_ids = {item.id for item in incidents if item.severity is Severity.CRITICAL}
    distances = [item.distance for item in result.assignments]
    return {
        "average_distance_km": sum(distances) / len(distances) if distances else 0.0,
        "coverage_percent": 100.0 * len(assigned_ids) / len(incidents) if incidents else 0.0,
        "critical_coverage_percent": (
            100.0 * len(assigned_ids & critical_ids) / len(critical_ids) if critical_ids else 100.0
        ),
    }
