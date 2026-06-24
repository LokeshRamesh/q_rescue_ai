from q_rescue.domain.models import Ambulance, Assignment, Incident, OptimizationResult
from q_rescue.quantum.qaoa_solver import ExactQuboSolver, QuboSolver
from q_rescue.quantum.qubo import AmbulanceAllocationQuboBuilder
from q_rescue.simulation.distance_matrix import DistanceMatrix, SeverityMapping


class QuantumAllocator:
    def __init__(
        self,
        builder: AmbulanceAllocationQuboBuilder | None = None,
        solver: QuboSolver | None = None,
    ) -> None:
        self.builder = builder or AmbulanceAllocationQuboBuilder()
        self.solver = solver or ExactQuboSolver()

    def solve(
        self,
        ambulances: list[Ambulance],
        incidents: list[Incident],
        distance_matrix: DistanceMatrix,
        severity_mapping: SeverityMapping,
    ) -> OptimizationResult:
        model = self.builder.build(ambulances, incidents, distance_matrix, severity_mapping)
        sample, objective_value = self.solver.solve(model)

        assignments = [
            Assignment(
                ambulance_id=ambulance_id,
                incident_id=incident_id,
                distance=distance_matrix.matrix[ambulance_id][incident_id],
            )
            for (ambulance_id, incident_id), selected in sample.items()
            if selected
        ]
        return OptimizationResult(
            assignments=assignments,
            objective_value=objective_value,
            solver_name=self.solver.name,
            feasible=self._is_feasible(assignments),
            metadata={"binary_variables": len(model.variables)},
        )

    @staticmethod
    def _is_feasible(assignments: list[Assignment]) -> bool:
        ambulance_ids = [item.ambulance_id for item in assignments]
        incident_ids = [item.incident_id for item in assignments]
        return len(ambulance_ids) == len(set(ambulance_ids)) and len(incident_ids) == len(
            set(incident_ids)
        )
