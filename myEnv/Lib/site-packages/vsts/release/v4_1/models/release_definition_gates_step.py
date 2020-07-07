# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseDefinitionGatesStep(Model):
    """ReleaseDefinitionGatesStep.

    :param gates:
    :type gates: list of :class:`ReleaseDefinitionGate <release.v4_1.models.ReleaseDefinitionGate>`
    :param gates_options:
    :type gates_options: :class:`ReleaseDefinitionGatesOptions <release.v4_1.models.ReleaseDefinitionGatesOptions>`
    :param id:
    :type id: int
    """

    _attribute_map = {
        'gates': {'key': 'gates', 'type': '[ReleaseDefinitionGate]'},
        'gates_options': {'key': 'gatesOptions', 'type': 'ReleaseDefinitionGatesOptions'},
        'id': {'key': 'id', 'type': 'int'}
    }

    def __init__(self, gates=None, gates_options=None, id=None):
        super(ReleaseDefinitionGatesStep, self).__init__()
        self.gates = gates
        self.gates_options = gates_options
        self.id = id
