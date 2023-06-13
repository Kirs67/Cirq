# Copyright 2018 The Cirq Developers
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

import cirq
import cirq.contrib.qpic as ccq
import cirq.testing as ct


def assert_has_qpic_representation(actual: cirq.Circuit, desired: str, **kwargs) -> None:
    """Determines if a given circuit has the desired QPIC language representation.

    Args:
        actual: The circuit that was actually computed by some process.
        desired: The desired QPIC language representation as a string. Newlines at the
            beginning and whitespace at the end are ignored.
        **kwargs: Keyword arguments to be passed to
            circuit_to_qpic_lang.
    """
    actual_diagram = ccq.circuit_to_qpic_lang(actual, **kwargs).lstrip('\n').rstrip()
    desired_diagram = desired.lstrip("\n").rstrip()
    assert actual_diagram == desired_diagram, (
        "Circuit's QPIC language representation differs from the desired.\n"
        '\n'
        'Actual circuit representation:\n'
        '{}\n'
        '\n'
        'Desired representation:\n'
        '{}\n'
        '\n'
        'Highlighted differences:\n'
        '{}\n'.format(
            actual_diagram,
            desired_diagram,
            ct.highlight_text_differences(actual_diagram, desired_diagram),
        )
    )


def test_fallback_diagram():
    class MagicGate(cirq.testing.ThreeQubitGate):
        def __str__(self):
            return 'MagicGate'

    class MagicOp(cirq.Operation):
        def __init__(self, *qubits):
            self._qubits = qubits

        def with_qubits(self, *new_qubits):
            return MagicOp(*new_qubits)

        @property
        def qubits(self):
            return self._qubits

        def __str__(self):
            return 'MagicOperate'

    circuit = cirq.Circuit(
        MagicOp(cirq.NamedQubit('b')),
        MagicGate().on(cirq.NamedQubit('b'), cirq.NamedQubit('a'), cirq.NamedQubit('c')),
    )
    expected_diagram = r"""
a W a
b W b
c W c
b G MagicOperate width=72
a b c G MagicGate width=54
""".strip()
    assert_has_qpic_representation(circuit, expected_diagram)


def test_teleportation_diagram():
    ali = cirq.NamedQubit('alice')
    car = cirq.NamedQubit('carrier')
    bob = cirq.NamedQubit('bob')

    circuit = cirq.Circuit(
        cirq.H(car),
        cirq.CNOT(car, bob),
        cirq.X(ali) ** 0.5,
        cirq.CNOT(ali, car),
        cirq.H(ali),
        [cirq.measure(ali), cirq.measure(car)],
        cirq.CNOT(car, bob),
        cirq.CZ(ali, bob),
    )

    expected_representation = r"""
alice W alice
carrier W carrier
bob W bob
carrier H
alice G $X^{0.5}$ width=24
bob C carrier
carrier C alice
alice H
carrier M
alice M
bob C carrier
alice bob
""".strip()
    assert_has_qpic_representation(
        circuit, expected_representation, qubit_order=cirq.QubitOrder.explicit([ali, car, bob])
    )


def test_other_diagram():
    a, b, c = cirq.LineQubit.range(3)

    circuit = cirq.Circuit(cirq.X(a), cirq.Y(b), cirq.Z(c))

    expected_diagram = r"""
q(0) W q(0)
q(1) W q(1)
q(2) W q(2)
q(0) X
q(1) G Y
q(2) Z
""".strip()
    assert_has_qpic_representation(circuit, expected_diagram)


def test_qpic_qubit_namer():
    from cirq.contrib.qpic import qpic_diagram

    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q')) == r'q'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q_1')) == r'q_1'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q^1')) == r'q^1'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q_{1}')) == r'q_1'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q_\1')) == r'q_1'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q_#1')) == r'q_1'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q_$1')) == r'q_1'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q_%1')) == r'q_1'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q_=1')) == r'q_1'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q_@1')) == r'q_1'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q_"1')) == r'q_1'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q_:1')) == r'q_1'
    assert qpic_diagram.qpic_qubit_namer(cirq.NamedQubit(r'q_1;')) == r'q_1'


def test_two_cx_diagram():
    # test for no moment indication
    q0, q1, q2, q3 = cirq.LineQubit.range(4)
    circuit = cirq.Circuit(cirq.CX(q0, q2), cirq.CX(q1, q3), cirq.CX(q0, q2), cirq.CX(q1, q3))
    expected_diagram = r"""
q(0) W q(0)
q(1) W q(1)
q(2) W q(2)
q(3) W q(3)
q(2) C q(0)
q(3) C q(1)
q(2) C q(0)
q(3) C q(1)
""".strip()
    assert_has_qpic_representation(circuit, expected_diagram)


def test_sqrt_iswap_diagram():
    # test for proper rendering of ISWAP^{0.5}
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.ISWAP(q0, q1) ** 0.5)
    expected_diagram = r"""
q(0) W q(0)
q(1) W q(1)
q(0) q(1) G $ISWAP^{0.5}$ width=48
""".strip()
    assert_has_qpic_representation(circuit, expected_diagram)


def test_parametrized_diagram():
    a, b, c = cirq.LineQubit.range(3)

    circuit = cirq.Circuit(cirq.X(a), cirq.Y(b), cirq.Z(c))

    expected_diagram = r"""
HEADER TEST DIAGRAM
VERTICAL
WIREPAD 10
q(0) W q(0)
q(1) W q(1)
q(2) W q(2)
q(0) X
q(1) G Y
q(2) Z
""".strip()
    assert_has_qpic_representation(circuit, expected_diagram, header="TEST DIAGRAM", vertical=True, wirepad=10)
