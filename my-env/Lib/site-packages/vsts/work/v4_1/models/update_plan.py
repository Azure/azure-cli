# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UpdatePlan(Model):
    """UpdatePlan.

    :param description: Description of the plan
    :type description: str
    :param name: Name of the plan to create.
    :type name: str
    :param properties: Plan properties.
    :type properties: object
    :param revision: Revision of the plan that was updated - the value used here should match the one the server gave the client in the Plan.
    :type revision: int
    :param type: Type of the plan
    :type type: object
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'properties': {'key': 'properties', 'type': 'object'},
        'revision': {'key': 'revision', 'type': 'int'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, description=None, name=None, properties=None, revision=None, type=None):
        super(UpdatePlan, self).__init__()
        self.description = description
        self.name = name
        self.properties = properties
        self.revision = revision
        self.type = type
