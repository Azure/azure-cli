# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ClientContribution(Model):
    """ClientContribution.

    :param description: Description of the contribution/type
    :type description: str
    :param id: Fully qualified identifier of the contribution/type
    :type id: str
    :param includes: Includes is a set of contributions that should have this contribution included in their targets list.
    :type includes: list of str
    :param properties: Properties/attributes of this contribution
    :type properties: :class:`object <contributions.v4_1.models.object>`
    :param targets: The ids of the contribution(s) that this contribution targets. (parent contributions)
    :type targets: list of str
    :param type: Id of the Contribution Type
    :type type: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'includes': {'key': 'includes', 'type': '[str]'},
        'properties': {'key': 'properties', 'type': 'object'},
        'targets': {'key': 'targets', 'type': '[str]'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, description=None, id=None, includes=None, properties=None, targets=None, type=None):
        super(ClientContribution, self).__init__()
        self.description = description
        self.id = id
        self.includes = includes
        self.properties = properties
        self.targets = targets
        self.type = type
