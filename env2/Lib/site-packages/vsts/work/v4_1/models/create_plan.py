# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CreatePlan(Model):
    """CreatePlan.

    :param description: Description of the plan
    :type description: str
    :param name: Name of the plan to create.
    :type name: str
    :param properties: Plan properties.
    :type properties: object
    :param type: Type of plan to create.
    :type type: object
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'properties': {'key': 'properties', 'type': 'object'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, description=None, name=None, properties=None, type=None):
        super(CreatePlan, self).__init__()
        self.description = description
        self.name = name
        self.properties = properties
        self.type = type
