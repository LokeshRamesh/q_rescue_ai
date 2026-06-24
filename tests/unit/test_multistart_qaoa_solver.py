import pytest

from q_rescue.quantum.qaoa_solver import MultiStartQAOASolver
from q_rescue.quantum.qubo import QuboModel, Variable


class _FakeSolver:
    name = "fake-qaoa"

    def __init__(self, sample: dict[Variable, int], value: float) -> None:
        self.sample = sample
        self.value = value

    def solve(self, model: QuboModel) -> tuple[dict[Variable, int], float]:
        return self.sample, self.value


def test_multistart_qaoa_keeps_lowest_energy_attempt() -> None:
    variable = ("A1", "I1")
    model = QuboModel(linear={variable: -1.0})
    samples = [
        {variable: 0},
        {variable: 1},
        {variable: 0},
    ]
    values = [4.0, -1.0, 2.0]
    seen_seeds: list[int] = []

    def solver_factory(seed: int) -> _FakeSolver:
        attempt_index = len(seen_seeds)
        seen_seeds.append(seed)
        return _FakeSolver(samples[attempt_index], values[attempt_index])

    solver = MultiStartQAOASolver(attempts=3, seed=42, solver_factory=solver_factory)

    sample, value = solver.solve(model)

    assert sample == {variable: 1}
    assert value == pytest.approx(-1.0)
    assert seen_seeds == solver.attempt_seeds


def test_multistart_qaoa_attempt_seeds_are_deterministic() -> None:
    first = MultiStartQAOASolver(attempts=4, seed=42)
    second = MultiStartQAOASolver(attempts=4, seed=42)

    assert first.attempt_seeds == second.attempt_seeds


def test_single_multistart_attempt_preserves_configured_seed() -> None:
    solver = MultiStartQAOASolver(attempts=1, seed=42)

    assert solver.attempt_seeds == [42]


def test_multistart_qaoa_rejects_invalid_attempt_count() -> None:
    with pytest.raises(ValueError, match="attempts"):
        MultiStartQAOASolver(attempts=0)
