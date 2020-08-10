# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AttributeDescriptor(Model):
    """AttributeDescriptor.

    :param attribute_name:
    :type attribute_name: str
    :param container_name:
    :type container_name: str
    """

    _attribute_map = {
        'attribute_name': {'key': 'attributeName', 'type': 'str'},
        'container_name': {'key': 'containerName', 'type': 'str'}
    }

    def __init__(self, attribute_name=None, container_name=None):
        super(AttributeDescriptor, self).__init__()
        self.attribute_name = attribute_name
        self.container_name = container_name
