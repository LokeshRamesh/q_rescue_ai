from __future__ import annotations

from itertools import product
from collections.abc import Callable
from typing import Protocol

import numpy as np

from q_rescue.quantum.qiskit_adapter import to_quadratic_program
from q_rescue.quantum.qubo import QuboModel, Variable


class QuboSolver(Protocol):
    name: str

    def solve(self, model: QuboModel) -> tuple[dict[Variable, int], float]: ...


class ExactQuboSolver:
    """Dependency-free POC solver. Use only for small validation scenarios."""

    name = "exact-enumeration"

    def solve(self, model: QuboModel) -> tuple[dict[Variable, int], float]:
        variables = model.variables
        if len(variables) > 24:
            raise ValueError("Exact enumeration is limited to 24 binary variables")

        best_sample: dict[Variable, int] = {}
        best_value = float("inf")
        for bits in product((0, 1), repeat=len(variables)):
            sample = dict(zip(variables, bits, strict=True))
            value = model.evaluate(sample)
            if value < best_value:
                best_sample = sample
                best_value = value
        return best_sample, best_value


class QiskitQAOASolver:
    """Member 1 integration boundary for Qiskit Optimization and QAOA."""

    name = "qiskit-qaoa"

    def __init__(
        self,
        reps: int = 1,
        shots: int = 1024,
        seed: int = 42,
        maxiter: int = 100,
    ) -> None:
        if reps < 1:
            raise ValueError("QAOA reps must be at least 1")
        if shots < 1:
            raise ValueError("QAOA shots must be at least 1")
        if maxiter < 1:
            raise ValueError("COBYLA maxiter must be at least 1")

        self.reps = reps
        self.shots = shots
        self.seed = seed
        self.maxiter = maxiter

    def solve(self, model: QuboModel) -> tuple[dict[Variable, int], float]:
        try:
            from qiskit.primitives import StatevectorSampler
            from qiskit_optimization.algorithms import MinimumEigenOptimizer
            from qiskit_optimization.minimum_eigensolvers import QAOA
            from qiskit_optimization.optimizers import COBYLA
        except ImportError as error:
            raise ImportError(
                "Qiskit quantum dependencies are required for QAOA. "
                'Install them with: pip install -e ".[quantum]"'
            ) from error

        conversion = to_quadratic_program(model)
        sampler = StatevectorSampler(default_shots=self.shots, seed=self.seed)
        optimizer = COBYLA(maxiter=self.maxiter)
        initial_point = np.random.default_rng(self.seed).uniform(
            0.0,
            2 * np.pi,
            2 * self.reps,
        )
        qaoa = QAOA(
            sampler=sampler,
            optimizer=optimizer,
            reps=self.reps,
            initial_point=initial_point,
        )
        result = MinimumEigenOptimizer(qaoa).solve(conversion.program)

        if result.x is None:
            raise RuntimeError("QAOA did not return a binary solution")

        named_sample = {name: round(value) for name, value in result.variables_dict.items()}
        sample = conversion.decode_sample(named_sample)
        return sample, model.evaluate(sample)


class MultiStartQAOASolver:
    """Run QAOA multiple times and keep the lowest-energy sample."""

    name = "qiskit-qaoa-multistart"

    def __init__(
        self,
        reps: int = 1,
        shots: int = 2048,
        seed: int = 42,
        maxiter: int = 100,
        attempts: int = 4,
        solver_factory: Callable[[int], QuboSolver] | None = None,
    ) -> None:
        if attempts < 1:
            raise ValueError("QAOA attempts must be at least 1")

        self.reps = reps
        self.shots = shots
        self.seed = seed
        self.maxiter = maxiter
        self.attempts = attempts
        self.attempt_seeds = self._generate_attempt_seeds(seed, attempts)
        self._solver_factory = solver_factory or self._build_single_run_solver

    def solve(self, model: QuboModel) -> tuple[dict[Variable, int], float]:
        best_sample: dict[Variable, int] | None = None
        best_value = float("inf")

        for seed in self.attempt_seeds:
            solver = self._solver_factory(seed)
            sample, value = solver.solve(model)
            if value < best_value:
                best_sample = sample
                best_value = value

        if best_sample is None:
            raise RuntimeError("Multi-start QAOA did not run any attempts")
        return best_sample, best_value

    def _build_single_run_solver(self, seed: int) -> QiskitQAOASolver:
        return QiskitQAOASolver(
            reps=self.reps,
            shots=self.shots,
            seed=seed,
            maxiter=self.maxiter,
        )

    @staticmethod
    def _generate_attempt_seeds(seed: int, attempts: int) -> list[int]:
        if attempts == 1:
            return [seed]
        return np.random.default_rng(seed).integers(0, 2**31 - 1, size=attempts).tolist()
