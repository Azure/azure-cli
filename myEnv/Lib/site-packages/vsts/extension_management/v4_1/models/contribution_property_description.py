# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ContributionPropertyDescription(Model):
    """ContributionPropertyDescription.

    :param description: Description of the property
    :type description: str
    :param name: Name of the property
    :type name: str
    :param required: True if this property is required
    :type required: bool
    :param type: The type of value used for this property
    :type type: object
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'required': {'key': 'required', 'type': 'bool'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, description=None, name=None, required=None, type=None):
        super(ContributionPropertyDescription, self).__init__()
        self.description = description
        self.name = name
        self.required = required
        self.type = type
