# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class VariableGroupParameters(Model):
    """VariableGroupParameters.

    :param description: Sets description of the variable group.
    :type description: str
    :param name: Sets name of the variable group.
    :type name: str
    :param provider_data: Sets provider data.
    :type provider_data: :class:`VariableGroupProviderData <task-agent.v4_1.models.VariableGroupProviderData>`
    :param type: Sets type of the variable group.
    :type type: str
    :param variables: Sets variables contained in the variable group.
    :type variables: dict
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'provider_data': {'key': 'providerData', 'type': 'VariableGroupProviderData'},
        'type': {'key': 'type', 'type': 'str'},
        'variables': {'key': 'variables', 'type': '{VariableValue}'}
    }

    def __init__(self, description=None, name=None, provider_data=None, type=None, variables=None):
        super(VariableGroupParameters, self).__init__()
        self.description = description
        self.name = name
        self.provider_data = provider_data
        self.type = type
        self.variables = variables
