# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PackageVersionDetails(Model):
    """PackageVersionDetails.

    :param deprecate_message: Indicates the deprecate message of a package version
    :type deprecate_message: str
    :param views: The view to which the package version will be added
    :type views: :class:`JsonPatchOperation <npm.v4_1.models.JsonPatchOperation>`
    """

    _attribute_map = {
        'deprecate_message': {'key': 'deprecateMessage', 'type': 'str'},
        'views': {'key': 'views', 'type': 'JsonPatchOperation'}
    }

    def __init__(self, deprecate_message=None, views=None):
        super(PackageVersionDetails, self).__init__()
        self.deprecate_message = deprecate_message
        self.views = views
