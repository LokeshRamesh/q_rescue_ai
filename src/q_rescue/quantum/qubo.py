from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

from q_rescue.domain.models import Ambulance, Incident
from q_rescue.simulation.distance_matrix import DistanceMatrix, SeverityMapping

Variable = tuple[str, str]
QuadraticTerm = tuple[Variable, Variable]


@dataclass
class QuboModel:
    """Framework-neutral QUBO representation: x^T Q x + constant."""

    objective_linear: dict[Variable, float] = field(default_factory=dict)
    linear: dict[Variable, float] = field(default_factory=dict)
    quadratic: dict[QuadraticTerm, float] = field(default_factory=dict)
    constant: float = 0.0

    @property
    def variables(self) -> list[Variable]:
        return list(self.linear)

    def evaluate(self, sample: dict[Variable, int]) -> float:
        value = self.constant
        value += sum(
            coefficient * sample.get(variable, 0) for variable, coefficient in self.linear.items()
        )
        value += sum(
            coefficient * sample.get(left, 0) * sample.get(right, 0)
            for (left, right), coefficient in self.quadratic.items()
        )
        return value


class AmbulanceAllocationQuboBuilder:
    """Build a POC QUBO for one-to-one ambulance/incident assignment.

    The solver now accepts a pre-computed ``DistanceMatrix`` and
    ``SeverityMapping`` from the simulation layer (Member 2), and applies
    the objective function internally:

        cost(a, i) = distance_weight × d(a, i) − severity_weight × s(i)

    A negative cost is expected for high-severity incidents: the QUBO
    minimiser is attracted toward strongly negative entries.
    """

    def __init__(
        self,
        distance_weight: float = 1.0,
        severity_weight: float = 1.0,
        constraint_penalty: float = 100.0,
    ) -> None:
        self.distance_weight = distance_weight
        self.severity_weight = severity_weight
        self.constraint_penalty = constraint_penalty

    def build(
        self,
        ambulances: list[Ambulance],
        incidents: list[Incident],
        distance_matrix: DistanceMatrix,
        severity_mapping: SeverityMapping,
    ) -> QuboModel:
        """Construct the QUBO model from pre-computed simulation outputs.

        Args:
            ambulances:       Ambulance list from the scenario.
            incidents:        Incident list from the scenario.
            distance_matrix:  Raw distances (km) from ``build_distance_matrix()``.
            severity_mapping: Absolute severity weights from ``build_severity_mapping()``.

        Returns:
            A populated ``QuboModel`` ready for the Qiskit solver.
        """
        model = QuboModel()

        for ambulance in ambulances:
            for incident in incidents:
                variable = (ambulance.id, incident.id)
                distance = distance_matrix.matrix[ambulance.id][incident.id]
                severity = severity_mapping[incident.id]
                # Normalise severity to 0–1 range (schema: 25/50/75/100 → 0.25…1.0)
                severity_normalised = severity / 100.0
                assignment_cost = (
                    self.distance_weight * distance - self.severity_weight * severity_normalised
                )
                model.objective_linear[variable] = assignment_cost
                model.linear[variable] = assignment_cost

        assignment_target = min(len(ambulances), len(incidents))
        self._add_cardinality_penalty(model, model.variables, assignment_target)

        for ambulance in ambulances:
            variables = [(ambulance.id, incident.id) for incident in incidents]
            self._add_exclusion_penalties(model, variables)

        for incident in incidents:
            variables = [(ambulance.id, incident.id) for ambulance in ambulances]
            self._add_exclusion_penalties(model, variables)

        return model

    def _add_cardinality_penalty(
        self,
        model: QuboModel,
        variables: list[Variable],
        target: int,
    ) -> None:
        """Add P(target - sum(x))^2 using x^2 = x for binary variables."""
        penalty = self.constraint_penalty
        model.constant += penalty * target**2

        for variable in variables:
            model.linear[variable] += penalty * (1 - 2 * target)

        for left, right in combinations(variables, 2):
            model.quadratic[(left, right)] = model.quadratic.get((left, right), 0.0) + 2 * penalty

    def _add_exclusion_penalties(self, model: QuboModel, variables: list[Variable]) -> None:
        for left, right in combinations(variables, 2):
            model.quadratic[(left, right)] = (
                model.quadratic.get((left, right), 0.0) + self.constraint_penalty
            )
