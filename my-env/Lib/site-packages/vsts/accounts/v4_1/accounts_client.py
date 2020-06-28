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


class AccountsClient(VssClient):
    """Accounts
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(AccountsClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '0d55247a-1c47-4462-9b1f-5e2125590ee6'

    def get_accounts(self, owner_id=None, member_id=None, properties=None):
        """GetAccounts.
        Get a list of accounts for a specific owner or a specific member.
        :param str owner_id: ID for the owner of the accounts.
        :param str member_id: ID for a member of the accounts.
        :param str properties:
        :rtype: [Account]
        """
        query_parameters = {}
        if owner_id is not None:
            query_parameters['ownerId'] = self._serialize.query('owner_id', owner_id, 'str')
        if member_id is not None:
            query_parameters['memberId'] = self._serialize.query('member_id', member_id, 'str')
        if properties is not None:
            query_parameters['properties'] = self._serialize.query('properties', properties, 'str')
        response = self._send(http_method='GET',
                              location_id='229a6a53-b428-4ffb-a835-e8f36b5b4b1e',
                              version='4.1',
                              query_parameters=query_parameters)
        return self._deserialize('[Account]', self._unwrap_collection(response))

