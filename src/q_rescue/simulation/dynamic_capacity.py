"""Dynamic hospital capacity simulation.

Provides functions to adjust hospital available beds dynamically based on
the severity and scale of the simulated disaster.
"""

from __future__ import annotations

from random import Random

from q_rescue.domain.models import Hospital


def simulate_hospital_load(
    hospitals: list[Hospital],
    incident_count: int,
    rng: Random,
    base_occupancy_pct: float = 0.65,
) -> list[Hospital]:
    """Simulate bed occupancy based on general system pressure.

    Args:
        hospitals: List of hospitals with baseline capacity data.
        incident_count: Total incidents in the scenario (higher means more pressure).
        rng: Seeded random number generator for deterministic variance.
        base_occupancy_pct: The typical background occupancy rate.

    Returns:
        A new list of hospitals with updated `available_beds`.
    """
    # Pressure factor scales with incident count (10 incidents = +5% occupancy)
    pressure_factor = (incident_count / 10.0) * 0.05

    updated_hospitals = []
    for h in hospitals:
        # Each hospital has slightly different background pressure (+/- 10%)
        variance = rng.uniform(-0.10, 0.10)

        target_occupancy = base_occupancy_pct + pressure_factor + variance
        # Cap at 100% occupancy (0 available beds)
        target_occupancy = min(1.0, max(0.0, target_occupancy))

        available = int(h.capacity * (1.0 - target_occupancy))

        updated_hospitals.append(
            Hospital(
                id=h.id,
                name=h.name,
                location=h.location,
                capacity=h.capacity,
                available_beds=available,
            )
        )

    return updated_hospitals
