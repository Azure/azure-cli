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

    def create_account(self, info, use_precreated=None):
        """CreateAccount.
        :param :class:`<AccountCreateInfoInternal> <accounts.v4_0.models.AccountCreateInfoInternal>` info:
        :param bool use_precreated:
        :rtype: :class:`<Account> <accounts.v4_0.models.Account>`
        """
        query_parameters = {}
        if use_precreated is not None:
            query_parameters['usePrecreated'] = self._serialize.query('use_precreated', use_precreated, 'bool')
        content = self._serialize.body(info, 'AccountCreateInfoInternal')
        response = self._send(http_method='POST',
                              location_id='229a6a53-b428-4ffb-a835-e8f36b5b4b1e',
                              version='4.0',
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('Account', response)

    def get_account(self, account_id):
        """GetAccount.
        :param str account_id:
        :rtype: :class:`<Account> <accounts.v4_0.models.Account>`
        """
        route_values = {}
        if account_id is not None:
            route_values['accountId'] = self._serialize.url('account_id', account_id, 'str')
        response = self._send(http_method='GET',
                              location_id='229a6a53-b428-4ffb-a835-e8f36b5b4b1e',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('Account', response)

    def get_accounts(self, owner_id=None, member_id=None, properties=None):
        """GetAccounts.
        A new version GetAccounts API. Only supports limited set of parameters, returns a list of account ref objects that only contains AccountUrl, AccountName and AccountId information, will use collection host Id as the AccountId.
        :param str owner_id: Owner Id to query for
        :param str member_id: Member Id to query for
        :param str properties: Only support service URL properties
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
                              version='4.0',
                              query_parameters=query_parameters)
        return self._deserialize('[Account]', self._unwrap_collection(response))

    def get_account_settings(self):
        """GetAccountSettings.
        [Preview API]
        :rtype: {str}
        """
        response = self._send(http_method='GET',
                              location_id='4e012dd4-f8e1-485d-9bb3-c50d83c5b71b',
                              version='4.0-preview.1')
        return self._deserialize('{str}', self._unwrap_collection(response))

