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


class SymbolClient(VssClient):
    """Symbol
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(SymbolClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = 'af607f94-69ba-4821-8159-f04e37b66350'

    def check_availability(self):
        """CheckAvailability.
        [Preview API] Check the availability of symbol service. This includes checking for feature flag, and possibly license in future. Note this is NOT an anonymous endpoint, and the caller will be redirected to authentication before hitting it.
        """
        self._send(http_method='GET',
                   location_id='97c893cc-e861-4ef4-8c43-9bad4a963dee',
                   version='4.1-preview.1')

    def get_client(self, client_type):
        """GetClient.
        [Preview API] Get the client package.
        :param str client_type: Either "EXE" for a zip file containing a Windows symbol client (a.k.a. symbol.exe) along with dependencies, or "TASK" for a VSTS task that can be run on a VSTS build agent. All the other values are invalid. The parameter is case-insensitive.
        :rtype: object
        """
        route_values = {}
        if client_type is not None:
            route_values['clientType'] = self._serialize.url('client_type', client_type, 'str')
        response = self._send(http_method='GET',
                              location_id='79c83865-4de3-460c-8a16-01be238e0818',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('object', response)

    def head_client(self):
        """HeadClient.
        [Preview API] Get client version information.
        """
        self._send(http_method='HEAD',
                   location_id='79c83865-4de3-460c-8a16-01be238e0818',
                   version='4.1-preview.1')

    def create_requests(self, request_to_create):
        """CreateRequests.
        [Preview API] Create a new symbol request.
        :param :class:`<Request> <symbol.v4_1.models.Request>` request_to_create: The symbol request to create.
        :rtype: :class:`<Request> <symbol.v4_1.models.Request>`
        """
        content = self._serialize.body(request_to_create, 'Request')
        response = self._send(http_method='POST',
                              location_id='ebc09fe3-1b20-4667-abc5-f2b60fe8de52',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('Request', response)

    def create_requests_request_id_debug_entries(self, batch, request_id, collection):
        """CreateRequestsRequestIdDebugEntries.
        [Preview API] Create debug entries for a symbol request as specified by its identifier.
        :param :class:`<DebugEntryCreateBatch> <symbol.v4_1.models.DebugEntryCreateBatch>` batch: A batch that contains debug entries to create.
        :param str request_id: The symbol request identifier.
        :param str collection: A valid debug entry collection name. Must be "debugentries".
        :rtype: [DebugEntry]
        """
        route_values = {}
        if request_id is not None:
            route_values['requestId'] = self._serialize.url('request_id', request_id, 'str')
        query_parameters = {}
        if collection is not None:
            query_parameters['collection'] = self._serialize.query('collection', collection, 'str')
        content = self._serialize.body(batch, 'DebugEntryCreateBatch')
        response = self._send(http_method='POST',
                              location_id='ebc09fe3-1b20-4667-abc5-f2b60fe8de52',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('[DebugEntry]', self._unwrap_collection(response))

    def create_requests_request_name_debug_entries(self, batch, request_name, collection):
        """CreateRequestsRequestNameDebugEntries.
        [Preview API] Create debug entries for a symbol request as specified by its name.
        :param :class:`<DebugEntryCreateBatch> <symbol.v4_1.models.DebugEntryCreateBatch>` batch: A batch that contains debug entries to create.
        :param str request_name:
        :param str collection: A valid debug entry collection name. Must be "debugentries".
        :rtype: [DebugEntry]
        """
        query_parameters = {}
        if request_name is not None:
            query_parameters['requestName'] = self._serialize.query('request_name', request_name, 'str')
        if collection is not None:
            query_parameters['collection'] = self._serialize.query('collection', collection, 'str')
        content = self._serialize.body(batch, 'DebugEntryCreateBatch')
        response = self._send(http_method='POST',
                              location_id='ebc09fe3-1b20-4667-abc5-f2b60fe8de52',
                              version='4.1-preview.1',
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('[DebugEntry]', self._unwrap_collection(response))

    def delete_requests_request_id(self, request_id, synchronous=None):
        """DeleteRequestsRequestId.
        [Preview API] Delete a symbol request by request identifier.
        :param str request_id: The symbol request identifier.
        :param bool synchronous: If true, delete all the debug entries under this request synchronously in the current session. If false, the deletion will be postponed to a later point and be executed automatically by the system.
        """
        route_values = {}
        if request_id is not None:
            route_values['requestId'] = self._serialize.url('request_id', request_id, 'str')
        query_parameters = {}
        if synchronous is not None:
            query_parameters['synchronous'] = self._serialize.query('synchronous', synchronous, 'bool')
        self._send(http_method='DELETE',
                   location_id='ebc09fe3-1b20-4667-abc5-f2b60fe8de52',
                   version='4.1-preview.1',
                   route_values=route_values,
                   query_parameters=query_parameters)

    def delete_requests_request_name(self, request_name, synchronous=None):
        """DeleteRequestsRequestName.
        [Preview API] Delete a symbol request by request name.
        :param str request_name:
        :param bool synchronous: If true, delete all the debug entries under this request synchronously in the current session. If false, the deletion will be postponed to a later point and be executed automatically by the system.
        """
        query_parameters = {}
        if request_name is not None:
            query_parameters['requestName'] = self._serialize.query('request_name', request_name, 'str')
        if synchronous is not None:
            query_parameters['synchronous'] = self._serialize.query('synchronous', synchronous, 'bool')
        self._send(http_method='DELETE',
                   location_id='ebc09fe3-1b20-4667-abc5-f2b60fe8de52',
                   version='4.1-preview.1',
                   query_parameters=query_parameters)

    def get_requests_request_id(self, request_id):
        """GetRequestsRequestId.
        [Preview API] Get a symbol request by request identifier.
        :param str request_id: The symbol request identifier.
        :rtype: :class:`<Request> <symbol.v4_1.models.Request>`
        """
        route_values = {}
        if request_id is not None:
            route_values['requestId'] = self._serialize.url('request_id', request_id, 'str')
        response = self._send(http_method='GET',
                              location_id='ebc09fe3-1b20-4667-abc5-f2b60fe8de52',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('Request', response)

    def get_requests_request_name(self, request_name):
        """GetRequestsRequestName.
        [Preview API] Get a symbol request by request name.
        :param str request_name:
        :rtype: :class:`<Request> <symbol.v4_1.models.Request>`
        """
        query_parameters = {}
        if request_name is not None:
            query_parameters['requestName'] = self._serialize.query('request_name', request_name, 'str')
        response = self._send(http_method='GET',
                              location_id='ebc09fe3-1b20-4667-abc5-f2b60fe8de52',
                              version='4.1-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('Request', response)

    def update_requests_request_id(self, update_request, request_id):
        """UpdateRequestsRequestId.
        [Preview API] Update a symbol request by request identifier.
        :param :class:`<Request> <symbol.v4_1.models.Request>` update_request: The symbol request.
        :param str request_id: The symbol request identifier.
        :rtype: :class:`<Request> <symbol.v4_1.models.Request>`
        """
        route_values = {}
        if request_id is not None:
            route_values['requestId'] = self._serialize.url('request_id', request_id, 'str')
        content = self._serialize.body(update_request, 'Request')
        response = self._send(http_method='PATCH',
                              location_id='ebc09fe3-1b20-4667-abc5-f2b60fe8de52',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Request', response)

    def update_requests_request_name(self, update_request, request_name):
        """UpdateRequestsRequestName.
        [Preview API] Update a symbol request by request name.
        :param :class:`<Request> <symbol.v4_1.models.Request>` update_request: The symbol request.
        :param str request_name:
        :rtype: :class:`<Request> <symbol.v4_1.models.Request>`
        """
        query_parameters = {}
        if request_name is not None:
            query_parameters['requestName'] = self._serialize.query('request_name', request_name, 'str')
        content = self._serialize.body(update_request, 'Request')
        response = self._send(http_method='PATCH',
                              location_id='ebc09fe3-1b20-4667-abc5-f2b60fe8de52',
                              version='4.1-preview.1',
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('Request', response)

    def get_sym_srv_debug_entry_client_key(self, debug_entry_client_key):
        """GetSymSrvDebugEntryClientKey.
        [Preview API] Given a client key, returns the best matched debug entry.
        :param str debug_entry_client_key: A "client key" used by both ends of Microsoft's symbol protocol to identify a debug entry. The semantics of client key is governed by symsrv and is beyond the scope of this documentation.
        """
        route_values = {}
        if debug_entry_client_key is not None:
            route_values['debugEntryClientKey'] = self._serialize.url('debug_entry_client_key', debug_entry_client_key, 'str')
        self._send(http_method='GET',
                   location_id='9648e256-c9f9-4f16-8a27-630b06396942',
                   version='4.1-preview.1',
                   route_values=route_values)

