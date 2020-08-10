# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest import Serializer, Deserializer
from ...vss_client import VssClient


class FeedTokenClient(VssClient):
    """FeedToken
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(FeedTokenClient, self).__init__(base_url, creds)
        self._serialize = Serializer()
        self._deserialize = Deserializer()

    resource_area_identifier = 'cdeb6c7d-6b25-4d6f-b664-c2e3ede202e8'

    def get_personal_access_token(self, feed_name=None):
        """GetPersonalAccessToken.
        [Preview API]
        :param str feed_name:
        :rtype: object
        """
        route_values = {}
        if feed_name is not None:
            route_values['feedName'] = self._serialize.url('feed_name', feed_name, 'str')
        response = self._send(http_method='GET',
                              location_id='dfdb7ad7-3d8e-4907-911e-19b4a8330550',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('object', response)

