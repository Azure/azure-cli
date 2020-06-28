# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AttributesContainer(Model):
    """AttributesContainer.

    :param attributes:
    :type attributes: dict
    :param container_name:
    :type container_name: str
    :param revision:
    :type revision: int
    """

    _attribute_map = {
        'attributes': {'key': 'attributes', 'type': '{ProfileAttribute}'},
        'container_name': {'key': 'containerName', 'type': 'str'},
        'revision': {'key': 'revision', 'type': 'int'}
    }

    def __init__(self, attributes=None, container_name=None, revision=None):
        super(AttributesContainer, self).__init__()
        self.attributes = attributes
        self.container_name = container_name
        self.revision = revision
