from q_rescue.domain.models import Ambulance, Assignment, Incident, OptimizationResult
from q_rescue.simulation.distance_matrix import DistanceMatrix, SeverityMapping


class GreedyAllocator:
    """Severity-first nearest-ambulance baseline for Member 4.

    The allocator now accepts a pre-computed ``DistanceMatrix`` and
    ``SeverityMapping`` from the simulation layer (Member 2), so it no
    longer computes distances directly from ``Location`` objects.
    """

    name = "classical-greedy"

    def solve(
        self,
        ambulances: list[Ambulance],
        incidents: list[Incident],
        distance_matrix: DistanceMatrix,
        severity_mapping: SeverityMapping,
    ) -> OptimizationResult:
        """Assign ambulances greedily: highest-severity incidents first,
        closest available ambulance wins.

        Args:
            ambulances:       Ambulance list from the scenario.
            incidents:        Incident list from the scenario.
            distance_matrix:  Raw distances (km) from ``build_distance_matrix()``.
            severity_mapping: Absolute severity weights from ``build_severity_mapping()``.

        Returns:
            An ``OptimizationResult`` with the greedy assignment.
        """
        available = {ambulance.id: ambulance for ambulance in ambulances}
        assignments: list[Assignment] = []

        # Sort incidents by severity weight descending (CRITICAL=100 first)
        sorted_incidents = sorted(incidents, key=lambda i: severity_mapping[i.id], reverse=True)

        for incident in sorted_incidents:
            if not available:
                break
            # Pick the nearest available ambulance using pre-computed distances
            ambulance = min(
                available.values(),
                key=lambda a: distance_matrix.matrix[a.id][incident.id],
            )
            distance = distance_matrix.matrix[ambulance.id][incident.id]
            assignments.append(Assignment(ambulance.id, incident.id, distance))
            del available[ambulance.id]

        return OptimizationResult(
            assignments=assignments,
            objective_value=sum(item.distance for item in assignments),
            solver_name=self.name,
        )
