# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccessMapping(Model):
    """AccessMapping.

    :param access_point:
    :type access_point: str
    :param display_name:
    :type display_name: str
    :param moniker:
    :type moniker: str
    :param service_owner: The service which owns this access mapping e.g. TFS, ELS, etc.
    :type service_owner: str
    :param virtual_directory: Part of the access mapping which applies context after the access point of the server.
    :type virtual_directory: str
    """

    _attribute_map = {
        'access_point': {'key': 'accessPoint', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'moniker': {'key': 'moniker', 'type': 'str'},
        'service_owner': {'key': 'serviceOwner', 'type': 'str'},
        'virtual_directory': {'key': 'virtualDirectory', 'type': 'str'}
    }

    def __init__(self, access_point=None, display_name=None, moniker=None, service_owner=None, virtual_directory=None):
        super(AccessMapping, self).__init__()
        self.access_point = access_point
        self.display_name = display_name
        self.moniker = moniker
        self.service_owner = service_owner
        self.virtual_directory = virtual_directory
