# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ClientContributionProviderDetails(Model):
    """ClientContributionProviderDetails.

    :param display_name: Friendly name for the provider.
    :type display_name: str
    :param name: Unique identifier for this provider. The provider name can be used to cache the contribution data and refer back to it when looking for changes
    :type name: str
    :param properties: Properties associated with the provider
    :type properties: dict
    :param version: Version of contributions assoicated with this contribution provider.
    :type version: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'properties': {'key': 'properties', 'type': '{str}'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, display_name=None, name=None, properties=None, version=None):
        super(ClientContributionProviderDetails, self).__init__()
        self.display_name = display_name
        self.name = name
        self.properties = properties
        self.version = version
