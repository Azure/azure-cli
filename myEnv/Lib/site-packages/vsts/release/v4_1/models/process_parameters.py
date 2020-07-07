# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProcessParameters(Model):
    """ProcessParameters.

    :param data_source_bindings:
    :type data_source_bindings: list of :class:`DataSourceBindingBase <microsoft.-team-foundation.-distributed-task.-common.-contracts.v4_1.models.DataSourceBindingBase>`
    :param inputs:
    :type inputs: list of :class:`TaskInputDefinitionBase <microsoft.-team-foundation.-distributed-task.-common.-contracts.v4_1.models.TaskInputDefinitionBase>`
    :param source_definitions:
    :type source_definitions: list of :class:`TaskSourceDefinitionBase <microsoft.-team-foundation.-distributed-task.-common.-contracts.v4_1.models.TaskSourceDefinitionBase>`
    """

    _attribute_map = {
        'data_source_bindings': {'key': 'dataSourceBindings', 'type': '[DataSourceBindingBase]'},
        'inputs': {'key': 'inputs', 'type': '[TaskInputDefinitionBase]'},
        'source_definitions': {'key': 'sourceDefinitions', 'type': '[TaskSourceDefinitionBase]'}
    }

    def __init__(self, data_source_bindings=None, inputs=None, source_definitions=None):
        super(ProcessParameters, self).__init__()
        self.data_source_bindings = data_source_bindings
        self.inputs = inputs
        self.source_definitions = source_definitions
