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


class CustomerIntelligenceClient(VssClient):
    """CustomerIntelligence
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(CustomerIntelligenceClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = None

    def publish_events(self, events):
        """PublishEvents.
        [Preview API]
        :param [CustomerIntelligenceEvent] events:
        """
        content = self._serialize.body(events, '[CustomerIntelligenceEvent]')
        self._send(http_method='POST',
                   location_id='b5cc35c2-ff2b-491d-a085-24b6e9f396fd',
                   version='4.0-preview.1',
                   content=content)

