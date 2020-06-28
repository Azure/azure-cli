# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LocationServiceData(Model):
    """LocationServiceData.

    :param access_mappings: Data about the access mappings contained by this location service.
    :type access_mappings: list of :class:`AccessMapping <locations.v4_0.models.AccessMapping>`
    :param client_cache_fresh: Data that the location service holds.
    :type client_cache_fresh: bool
    :param client_cache_time_to_live: The time to live on the location service cache.
    :type client_cache_time_to_live: int
    :param default_access_mapping_moniker: The default access mapping moniker for the server.
    :type default_access_mapping_moniker: str
    :param last_change_id: The obsolete id for the last change that took place on the server (use LastChangeId64).
    :type last_change_id: int
    :param last_change_id64: The non-truncated 64-bit id for the last change that took place on the server.
    :type last_change_id64: long
    :param service_definitions: Data about the service definitions contained by this location service.
    :type service_definitions: list of :class:`ServiceDefinition <locations.v4_0.models.ServiceDefinition>`
    :param service_owner: The identifier of the deployment which is hosting this location data (e.g. SPS, TFS, ELS, Napa, etc.)
    :type service_owner: str
    """

    _attribute_map = {
        'access_mappings': {'key': 'accessMappings', 'type': '[AccessMapping]'},
        'client_cache_fresh': {'key': 'clientCacheFresh', 'type': 'bool'},
        'client_cache_time_to_live': {'key': 'clientCacheTimeToLive', 'type': 'int'},
        'default_access_mapping_moniker': {'key': 'defaultAccessMappingMoniker', 'type': 'str'},
        'last_change_id': {'key': 'lastChangeId', 'type': 'int'},
        'last_change_id64': {'key': 'lastChangeId64', 'type': 'long'},
        'service_definitions': {'key': 'serviceDefinitions', 'type': '[ServiceDefinition]'},
        'service_owner': {'key': 'serviceOwner', 'type': 'str'}
    }

    def __init__(self, access_mappings=None, client_cache_fresh=None, client_cache_time_to_live=None, default_access_mapping_moniker=None, last_change_id=None, last_change_id64=None, service_definitions=None, service_owner=None):
        super(LocationServiceData, self).__init__()
        self.access_mappings = access_mappings
        self.client_cache_fresh = client_cache_fresh
        self.client_cache_time_to_live = client_cache_time_to_live
        self.default_access_mapping_moniker = default_access_mapping_moniker
        self.last_change_id = last_change_id
        self.last_change_id64 = last_change_id64
        self.service_definitions = service_definitions
        self.service_owner = service_owner
