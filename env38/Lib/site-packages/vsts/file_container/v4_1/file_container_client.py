# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest import Serializer, Deserializer
from ...vss_client import VssClient
from . import models


class FileContainerClient(VssClient):
    """FileContainer
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(FileContainerClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = None

    def create_items(self, items, container_id, scope=None):
        """CreateItems.
        [Preview API] Creates the specified items in in the referenced container.
        :param :class:`<VssJsonCollectionWrapper> <file-container.v4_1.models.VssJsonCollectionWrapper>` items:
        :param int container_id:
        :param str scope: A guid representing the scope of the container. This is often the project id.
        :rtype: [FileContainerItem]
        """
        route_values = {}
        if container_id is not None:
            route_values['containerId'] = self._serialize.url('container_id', container_id, 'int')
        query_parameters = {}
        if scope is not None:
            query_parameters['scope'] = self._serialize.query('scope', scope, 'str')
        content = self._serialize.body(items, 'VssJsonCollectionWrapper')
        response = self._send(http_method='POST',
                              location_id='e4f5c81e-e250-447b-9fef-bd48471bea5e',
                              version='4.1-preview.4',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('[FileContainerItem]', self._unwrap_collection(response))

    def delete_item(self, container_id, item_path, scope=None):
        """DeleteItem.
        [Preview API] Deletes the specified items in a container.
        :param long container_id: Container Id.
        :param str item_path: Path to delete.
        :param str scope: A guid representing the scope of the container. This is often the project id.
        """
        route_values = {}
        if container_id is not None:
            route_values['containerId'] = self._serialize.url('container_id', container_id, 'long')
        query_parameters = {}
        if item_path is not None:
            query_parameters['itemPath'] = self._serialize.query('item_path', item_path, 'str')
        if scope is not None:
            query_parameters['scope'] = self._serialize.query('scope', scope, 'str')
        self._send(http_method='DELETE',
                   location_id='e4f5c81e-e250-447b-9fef-bd48471bea5e',
                   version='4.1-preview.4',
                   route_values=route_values,
                   query_parameters=query_parameters)

    def get_containers(self, scope=None, artifact_uris=None):
        """GetContainers.
        [Preview API] Gets containers filtered by a comma separated list of artifact uris within the same scope, if not specified returns all containers
        :param str scope: A guid representing the scope of the container. This is often the project id.
        :param str artifact_uris:
        :rtype: [FileContainer]
        """
        query_parameters = {}
        if scope is not None:
            query_parameters['scope'] = self._serialize.query('scope', scope, 'str')
        if artifact_uris is not None:
            query_parameters['artifactUris'] = self._serialize.query('artifact_uris', artifact_uris, 'str')
        response = self._send(http_method='GET',
                              location_id='e4f5c81e-e250-447b-9fef-bd48471bea5e',
                              version='4.1-preview.4',
                              query_parameters=query_parameters)
        return self._deserialize('[FileContainer]', self._unwrap_collection(response))

    def get_items(self, container_id, scope=None, item_path=None, metadata=None, format=None, download_file_name=None, include_download_tickets=None, is_shallow=None):
        """GetItems.
        [Preview API]
        :param long container_id:
        :param str scope:
        :param str item_path:
        :param bool metadata:
        :param str format:
        :param str download_file_name:
        :param bool include_download_tickets:
        :param bool is_shallow:
        :rtype: [FileContainerItem]
        """
        route_values = {}
        if container_id is not None:
            route_values['containerId'] = self._serialize.url('container_id', container_id, 'long')
        query_parameters = {}
        if scope is not None:
            query_parameters['scope'] = self._serialize.query('scope', scope, 'str')
        if item_path is not None:
            query_parameters['itemPath'] = self._serialize.query('item_path', item_path, 'str')
        if metadata is not None:
            query_parameters['metadata'] = self._serialize.query('metadata', metadata, 'bool')
        if format is not None:
            query_parameters['$format'] = self._serialize.query('format', format, 'str')
        if download_file_name is not None:
            query_parameters['downloadFileName'] = self._serialize.query('download_file_name', download_file_name, 'str')
        if include_download_tickets is not None:
            query_parameters['includeDownloadTickets'] = self._serialize.query('include_download_tickets', include_download_tickets, 'bool')
        if is_shallow is not None:
            query_parameters['isShallow'] = self._serialize.query('is_shallow', is_shallow, 'bool')
        response = self._send(http_method='GET',
                              location_id='e4f5c81e-e250-447b-9fef-bd48471bea5e',
                              version='4.1-preview.4',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[FileContainerItem]', self._unwrap_collection(response))

