"""Operational constraints for the Q-Rescue ambulance allocation problem.

``OperationalConstraints`` is the canonical constraint definition consumed by:
- The QUBO builder (Member 1) for penalty encoding
- The classical greedy allocator (Member 4) for feasibility checking
- The cost matrix builder for constraint-aware cost adjustments

It mirrors the logical structure of the QUBO penalty terms in
``src/q_rescue/quantum/qubo.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OperationalConstraints:
    """Defines the set of hard and soft operational constraints.

    All boolean flags default to ``True`` (fully constrained). Set a flag to
    ``False`` to relax that constraint (useful for benchmarking or debugging).

    Attributes:
        one_ambulance_per_incident:  Each incident receives at most one
                                     ambulance per allocation period.
        one_incident_per_ambulance:  Each ambulance attends at most one
                                     incident per allocation period.
        hospital_capacity_limit:     Routed patients cannot exceed a
                                     hospital's ``available_beds``.
        critical_priority:           Critical incidents must be assigned
                                     before lower-severity ones if possible.
        max_response_time_minutes:   Optional upper-bound on response time.
                                     ``None`` means unconstrained (future use).
        constraint_penalty:          QUBO quadratic penalty coefficient (λ)
                                     applied to each violated constraint pair.
                                     Maps to ``[optimisation] constraint_penalty``
                                     in ``configs/default.toml``.
    """

    one_ambulance_per_incident: bool = True
    one_incident_per_ambulance: bool = True
    hospital_capacity_limit: bool = True
    critical_priority: bool = True
    max_response_time_minutes: float | None = None
    constraint_penalty: float = 100.0

    # Penalty-coefficient metadata for QUBO builder documentation
    _penalty_terms: dict[str, str] = field(
        default_factory=lambda: {
            "one_ambulance_per_incident": "Σᵢ xᵢⱼ ≤ 1  ∀j",
            "one_incident_per_ambulance": "Σⱼ xᵢⱼ ≤ 1  ∀i",
            "hospital_capacity_limit": "Σ incidents(j→h) ≤ beds(h)",
        },
        repr=False,
    )

    @classmethod
    def from_config(cls, config: dict) -> "OperationalConstraints":
        """Instantiate from a config dict (matching ``configs/default.toml``).

        Reads:
        - ``[optimisation] constraint_penalty``
        - ``[constraints] *``  (optional — all default to True if absent)

        Args:
            config: Nested dict loaded from ``default.toml`` via ``tomllib``.

        Returns:
            A fully populated ``OperationalConstraints`` instance.
        """
        opt = config.get("optimisation", {})
        con = config.get("constraints", {})
        return cls(
            one_ambulance_per_incident=con.get("one_ambulance_per_incident", True),
            one_incident_per_ambulance=con.get("one_incident_per_ambulance", True),
            hospital_capacity_limit=con.get("hospital_capacity_limit", True),
            critical_priority=con.get("critical_priority", True),
            max_response_time_minutes=con.get("max_response_time_minutes", None),
            constraint_penalty=opt.get("constraint_penalty", 100.0),
        )

    def active_constraints(self) -> list[str]:
        """Return a list of human-readable active constraint names."""
        active = []
        if self.one_ambulance_per_incident:
            active.append("one_ambulance_per_incident")
        if self.one_incident_per_ambulance:
            active.append("one_incident_per_ambulance")
        if self.hospital_capacity_limit:
            active.append("hospital_capacity_limit")
        if self.critical_priority:
            active.append("critical_priority")
        if self.max_response_time_minutes is not None:
            active.append(f"max_response_time_minutes={self.max_response_time_minutes}")
        return active

    def to_dict(self) -> dict:
        """Serialise to a plain dict for JSON/CSV export."""
        return {
            "one_ambulance_per_incident": self.one_ambulance_per_incident,
            "one_incident_per_ambulance": self.one_incident_per_ambulance,
            "hospital_capacity_limit": self.hospital_capacity_limit,
            "critical_priority": self.critical_priority,
            "max_response_time_minutes": self.max_response_time_minutes,
            "constraint_penalty": self.constraint_penalty,
        }
