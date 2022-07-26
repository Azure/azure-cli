# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
import unittest
from unittest import mock
import os

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.mock import DummyCli
from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest
from knack.util import CLIError
from azure.cli.testsdk import live_only, MOCKED_USER_NAME
from azure.cli.testsdk.constants import AUX_SUBSCRIPTION, AUX_TENANT

from azure.cli.testsdk.scenario_tests.const import MOCKED_SUBSCRIPTION_ID, MOCKED_TENANT_ID

mock_subscriptions = [
    {
        "id": MOCKED_SUBSCRIPTION_ID,
        "state": "Enabled",
        "name": "Example",
        "tenantId": MOCKED_TENANT_ID,
        "isDefault": True,
        "user": {
            "name": MOCKED_USER_NAME,
            "type": "user"
        }
    },
    {
        "id": AUX_SUBSCRIPTION,
        "state": "Enabled",
        "name": "Auxiliary Subscription",
        "tenantId": AUX_TENANT,
        "isDefault": False,
        "user": {
            "name": MOCKED_USER_NAME,
            "type": "user"
        }
    }
]


class CredentialMock:
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._authority = kwargs.get('authority')

    def get_token(self, *scopes, **kwargs):  # pylint: disable=unused-argument
        from azure.core.credentials import AccessToken
        import time
        now = int(time.time())
        return AccessToken("access_token_from_" + self._authority, now + 3600)


class TestClientFactory(unittest.TestCase):
    def test_get_mgmt_service_client(self):
        cli = DummyCli()
        client = get_mgmt_service_client(cli, ResourceType.MGMT_RESOURCE_RESOURCES)
        assert client

    @mock.patch("azure.cli.core.auth.identity.UserCredential", CredentialMock)
    @mock.patch('azure.cli.core._profile.Profile.load_cached_subscriptions', return_value=mock_subscriptions)
    def test_get_mgmt_service_client_with_aux_subs_and_tenants(self, load_cached_subscriptions_mock):
        cli = DummyCli()

        def _verify_client_aux_token(client_to_check):
            aux_tokens = client_to_check._config.headers_policy.headers.get('x-ms-authorization-auxiliary')
            assert aux_tokens
            assert aux_tokens.startswith("Bearer ")
            assert AUX_TENANT in aux_tokens

        # Specify aux_subscriptions
        client = get_mgmt_service_client(cli, ResourceType.MGMT_RESOURCE_RESOURCES,
                                         aux_subscriptions=[AUX_SUBSCRIPTION])
        _verify_client_aux_token(client)

        # Specify aux_tenants
        client = get_mgmt_service_client(cli, ResourceType.MGMT_RESOURCE_RESOURCES,
                                         aux_tenants=[AUX_TENANT])
        _verify_client_aux_token(client)

        # But not both
        with self.assertRaisesRegex(CLIError, "only one of aux_subscriptions and aux_tenants"):
            get_mgmt_service_client(cli, ResourceType.MGMT_RESOURCE_RESOURCES,
                                    aux_subscriptions=[AUX_SUBSCRIPTION], aux_tenants=[AUX_TENANT])


if __name__ == '__main__':
    unittest.main()
