# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SecureFile(Model):
    """SecureFile.

    :param created_by:
    :type created_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param created_on:
    :type created_on: datetime
    :param id:
    :type id: str
    :param modified_by:
    :type modified_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param modified_on:
    :type modified_on: datetime
    :param name:
    :type name: str
    :param properties:
    :type properties: dict
    :param ticket:
    :type ticket: str
    """

    _attribute_map = {
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'modified_by': {'key': 'modifiedBy', 'type': 'IdentityRef'},
        'modified_on': {'key': 'modifiedOn', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'properties': {'key': 'properties', 'type': '{str}'},
        'ticket': {'key': 'ticket', 'type': 'str'}
    }

    def __init__(self, created_by=None, created_on=None, id=None, modified_by=None, modified_on=None, name=None, properties=None, ticket=None):
        super(SecureFile, self).__init__()
        self.created_by = created_by
        self.created_on = created_on
        self.id = id
        self.modified_by = modified_by
        self.modified_on = modified_on
        self.name = name
        self.properties = properties
        self.ticket = ticket
