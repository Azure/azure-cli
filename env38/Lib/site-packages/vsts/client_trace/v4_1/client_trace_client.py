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


class ClientTraceClient(VssClient):
    """ClientTrace
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(ClientTraceClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = None

    def publish_events(self, events):
        """PublishEvents.
        [Preview API]
        :param [ClientTraceEvent] events:
        """
        content = self._serialize.body(events, '[ClientTraceEvent]')
        self._send(http_method='POST',
                   location_id='06bcc74a-1491-4eb8-a0eb-704778f9d041',
                   version='4.1-preview.1',
                   content=content)

