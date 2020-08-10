# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging

from msrest.service_client import ServiceClient
from ._file_cache import RESOURCE_CACHE as RESOURCE_FILE_CACHE
from .exceptions import VstsClientRequestError
from .location.v4_0.location_client import LocationClient
from .vss_client_configuration import VssClientConfiguration

logger = logging.getLogger(__name__)


class VssConnection(object):
    """VssConnection.
    """

    def __init__(self, base_url=None, creds=None, user_agent=None):
        self._config = VssClientConfiguration(base_url)
        self._addition_user_agent = user_agent
        if user_agent is not None:
            self._config.add_user_agent(user_agent)
        self._client = ServiceClient(creds, self._config)
        self._client_cache = {}
        self.base_url = base_url
        self._creds = creds
        self._resource_areas = None

    def get_client(self, client_type):
        """get_client.
        """
        if client_type not in self._client_cache:
            client_class = self._get_class(client_type)
            self._client_cache[client_type] = self._get_client_instance(client_class)
        return self._client_cache[client_type]

    @staticmethod
    def _get_class(full_class_name):
        parts = full_class_name.split('.')
        module_name = ".".join(parts[:-1])
        imported = __import__(module_name)
        for comp in parts[1:]:
            imported = getattr(imported, comp)
        return imported

    def _get_client_instance(self, client_class):
        url = self._get_url_for_client_instance(client_class)
        client = client_class(url, self._creds)
        client.add_user_agent(self._addition_user_agent)
        return client

    def _get_url_for_client_instance(self, client_class):
        resource_id = client_class.resource_area_identifier
        if resource_id is None:
            return self.base_url
        else:
            resource_areas = self._get_resource_areas()
            if resource_areas is None:
                raise VstsClientRequestError(('Failed to retrieve resource areas '
                                              + 'from server: {url}').format(url=self.base_url))
            if not resource_areas:
                # For OnPrem environments we get an empty list.
                return self.base_url
            for resource_area in resource_areas:
                if resource_area.id.lower() == resource_id.lower():
                    return resource_area.location_url
            raise VstsClientRequestError(('Could not find information for resource area {id} '
                                          + 'from server: {url}').format(id=resource_id,
                                                                         url=self.base_url))

    def authenticate(self):
        self._get_resource_areas(force=True)

    def _get_resource_areas(self, force=False):
        if self._resource_areas is None or force:
            location_client = LocationClient(self.base_url, self._creds)
            if not force and RESOURCE_FILE_CACHE[location_client.normalized_url]:
                try:
                    logger.debug('File cache hit for resources on: %s', location_client.normalized_url)
                    self._resource_areas = location_client._base_deserialize.deserialize_data(RESOURCE_FILE_CACHE[location_client.normalized_url],
                                                                                              '[ResourceAreaInfo]')
                    return self._resource_areas
                except Exception as ex:
                    logger.debug(ex, exc_info=True)
            elif not force:
                logger.debug('File cache miss for resources on: %s', location_client.normalized_url)
            self._resource_areas = location_client.get_resource_areas()
            if self._resource_areas is None:
                # For OnPrem environments we get an empty collection wrapper.
                self._resource_areas = []
            try:
                serialized = location_client._base_serialize.serialize_data(self._resource_areas,
                                                                            '[ResourceAreaInfo]')
                RESOURCE_FILE_CACHE[location_client.normalized_url] = serialized
            except Exception as ex:
                logger.debug(ex, exc_info=True)
        return self._resource_areas

    @staticmethod
    def _combine_url(part1, part2):
        return part1.rstrip('/') + '/' + part2.strip('/')
