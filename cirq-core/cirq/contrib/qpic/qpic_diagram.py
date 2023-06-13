# Copyright 2023 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import TYPE_CHECKING, Optional, Union, Tuple, List
from numbers import Number

from cirq import circuits, ops

if TYPE_CHECKING:
    import cirq


def qpic_qubit_namer(qubit: 'cirq.Qid') -> str:
    """Returns a QPIC-appropriate name for the qubit.

    Args:
        qubit: The qubit which needs to be named.

    Returns:
        QPIC name for the qubit.
    """
    forbidden_symbols = r'\#${}%=@":;'

    name = str(qubit)
    name = name.translate(str.maketrans("", "", forbidden_symbols))

    if name[0] == '-':
        name = 'minus_' + name[1:]
    elif name[0] == '+':
        name = 'plus_' + name[1:]

    return name


def get_latex_name(op: ops.Operation) -> str:
    """Represent the operation name in a format that can be rendered in latex

    Args:
        op: the operation to be named

    Returns:
        Latex-formatted name for the operation
    """
    if op.gate:
        name = str(op.gate)
    else:
        name = str(op)

    if '**' in name:
        [base, exponent] = name.split('**', 1)
        name = f'${base}^{{{exponent}}}$'

    return name


def op_to_qpic(op: ops.Operation, qubit_order: 'cirq.QubitOrder') -> str:
    """Returns QPIC language representation for the operation.

    Args:
        op: the operation to represent
        qubit_order: Determines the order of qubit wires in targets/controls.

    Returns:
        QPIC language representation for the operation.
    """
    arguments = {}

    match op.gate:
        case ops.X:
            op_symbol = 'X'
            targets = op.qubits
            controls = []
        case ops.Z:
            op_symbol = 'Z'
            targets = op.qubits
            controls = []
        case ops.H:
            op_symbol = 'H'
            targets = op.qubits
            controls = []
        case ops.CNOT:
            op_symbol = 'C'
            targets = [op.qubits[1]]
            controls = [op.qubits[0]]
        case ops.CZ:
            op_symbol = ''
            targets = []
            controls = op.qubits
        case ops.SWAP:
            op_symbol = 'SWAP'
            targets = op.qubits
            controls = []
        case ops.TOFFOLI:
            op_symbol = 'T'
            targets = [op.qubits[2]]
            controls = op.qubits[0:2]
        case ops.MeasurementGate():
            op_symbol = 'M'
            targets = op.qubits
            controls = []
        case _:
            name = get_latex_name(op)
            op_symbol = f'G {name}'
            targets = op.qubits
            controls = []
            effective_len = len(name.replace('$', '').replace('^', '').replace('{', '').replace('}', ''))
            if effective_len > 1:
                arguments["width"] = effective_len*6

    ordered_targets = qubit_order.order_for(targets)
    targets = [q for q in ordered_targets if q in targets] #as the qubit order MIGHT spit out all the qubits
    targets = [qpic_qubit_namer(q) for q in targets]

    ordered_controls = qubit_order.order_for(controls)
    controls = [q for q in ordered_controls if q in controls] # same as for the targets
    controls = [qpic_qubit_namer(q) for q in controls]

    command = f'{" ".join(targets)} {op_symbol} {" ".join(controls)}'.strip()
    for argument, value in arguments.items():
        command += f' {argument}={value}'

    return command


def circuit_to_qpic_lang(
    circuit: 'cirq.Circuit', qubit_order: 'cirq.QubitOrderOrList' = ops.QubitOrder.DEFAULT, **kwargs
) -> str:
    """Returns QPIC language representation for the circuit which can be converted to LaTeX with qpic script.

    Args:
        circuit: The circuit to convert.
        qubit_order: Determines the order of qubit wires in the diagram.
        kwargs: can be used to insert macros or global parameters into the QPIC code. If the value is boolean, the
            capitalized key is inserted into the QPIC code (or not, depending on if the value is True), otherwise a line
            with capitalized key and then the value as a string is inserted. Consult the QPIC documentation for the list
            of the macros and parameters.

    Returns:
        QPIC language representation for the diagram.
    """
    qubit_order = ops.QubitOrder.as_qubit_order(qubit_order)
    qubits = qubit_order.order_for(circuit.all_qubits())
    names = [qpic_qubit_namer(q) for q in qubits]
    labels = [str(q) for q in qubits]

    declarations = [f"{n} W {l}" for (n, l) in zip(names, labels)]
    declarations = "\n".join(declarations)

    non_global_ops = []
    for moment in circuit.moments:
        non_global_ops.extend( [op for op in moment.operations if op.qubits] )

    operations = [op_to_qpic(op, qubit_order) for op in non_global_ops]
    operations = "\n".join(operations)

    preamble = []
    for (key, value) in kwargs.items():
        if isinstance(value, bool):
            if value:
                preamble.append(key.upper())
        else:
            preamble.append(f'{key.upper()} {value}')


    preamble = "\n".join(preamble)

    parts = [preamble, declarations, operations]
    parts = [p for p in parts if p]

    return "\n".join(parts)
