# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class VariableGroup(Model):
    """VariableGroup.

    :param created_by: Gets or sets the identity who created the variable group.
    :type created_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param created_on: Gets or sets the time when variable group was created.
    :type created_on: datetime
    :param description: Gets or sets description of the variable group.
    :type description: str
    :param id: Gets or sets id of the variable group.
    :type id: int
    :param modified_by: Gets or sets the identity who modified the variable group.
    :type modified_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param modified_on: Gets or sets the time when variable group was modified
    :type modified_on: datetime
    :param name: Gets or sets name of the variable group.
    :type name: str
    :param provider_data: Gets or sets provider data.
    :type provider_data: :class:`VariableGroupProviderData <task-agent.v4_1.models.VariableGroupProviderData>`
    :param type: Gets or sets type of the variable group.
    :type type: str
    :param variables: Gets or sets variables contained in the variable group.
    :type variables: dict
    """

    _attribute_map = {
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'modified_by': {'key': 'modifiedBy', 'type': 'IdentityRef'},
        'modified_on': {'key': 'modifiedOn', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'provider_data': {'key': 'providerData', 'type': 'VariableGroupProviderData'},
        'type': {'key': 'type', 'type': 'str'},
        'variables': {'key': 'variables', 'type': '{VariableValue}'}
    }

    def __init__(self, created_by=None, created_on=None, description=None, id=None, modified_by=None, modified_on=None, name=None, provider_data=None, type=None, variables=None):
        super(VariableGroup, self).__init__()
        self.created_by = created_by
        self.created_on = created_on
        self.description = description
        self.id = id
        self.modified_by = modified_by
        self.modified_on = modified_on
        self.name = name
        self.provider_data = provider_data
        self.type = type
        self.variables = variables
