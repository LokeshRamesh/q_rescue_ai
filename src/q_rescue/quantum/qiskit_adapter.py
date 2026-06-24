from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from q_rescue.quantum.qubo import QuboModel, Variable


@dataclass(frozen=True)
class QiskitQuboConversion:
    """Qiskit program plus the mappings needed to recover domain variables."""

    program: Any
    variable_to_name: dict[Variable, str]
    name_to_variable: dict[str, Variable]

    def decode_sample(self, sample: dict[str, int]) -> dict[Variable, int]:
        """Translate a Qiskit-name sample back to ambulance/incident tuples."""
        return {
            self.name_to_variable[name]: int(value)
            for name, value in sample.items()
            if name in self.name_to_variable
        }


def to_quadratic_program(
    model: QuboModel,
    name: str = "ambulance_allocation_qubo",
) -> QiskitQuboConversion:
    """Convert the framework-neutral QUBO into a Qiskit QuadraticProgram.

    Qiskit is imported inside the function so it remains an optional dependency
    for users running only the simulation or exact-enumeration workflow.
    """
    try:
        from qiskit_optimization import QuadraticProgram
    except ImportError as error:
        raise ImportError(
            "Qiskit Optimization is required for this conversion. "
            'Install it with: pip install -e ".[quantum]"'
        ) from error

    variable_to_name = {variable: f"x_{index}" for index, variable in enumerate(model.variables)}
    name_to_variable = {qiskit_name: variable for variable, qiskit_name in variable_to_name.items()}

    program = QuadraticProgram(name=name)
    for qiskit_name in name_to_variable:
        program.binary_var(name=qiskit_name)

    linear = {
        variable_to_name[variable]: coefficient for variable, coefficient in model.linear.items()
    }
    quadratic = {
        (variable_to_name[left], variable_to_name[right]): coefficient
        for (left, right), coefficient in model.quadratic.items()
    }
    program.minimize(
        constant=model.constant,
        linear=linear,
        quadratic=quadratic,
    )

    return QiskitQuboConversion(
        program=program,
        variable_to_name=variable_to_name,
        name_to_variable=name_to_variable,
    )
