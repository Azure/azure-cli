# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class VersionedResource(Model):
    """VersionedResource.

    :param compatible_with: Gets or sets the reference to the compatible version.
    :type compatible_with: str
    :param resource: Gets or sets the resource data.
    :type resource: object
    :param resource_version: Gets or sets the version of the resource data.
    :type resource_version: str
    """

    _attribute_map = {
        'compatible_with': {'key': 'compatibleWith', 'type': 'str'},
        'resource': {'key': 'resource', 'type': 'object'},
        'resource_version': {'key': 'resourceVersion', 'type': 'str'}
    }

    def __init__(self, compatible_with=None, resource=None, resource_version=None):
        super(VersionedResource, self).__init__()
        self.compatible_with = compatible_with
        self.resource = resource
        self.resource_version = resource_version
