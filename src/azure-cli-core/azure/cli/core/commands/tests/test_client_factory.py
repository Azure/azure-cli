# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
import unittest

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.mock import DummyCli
from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest
from knack.util import CLIError

AUX_SUBSCRIPTION = '1c638cf4-608f-4ee6-b680-c329e824c3a8'
AUX_TENANT = '72f988bf-86f1-41af-91ab-2d7cd011db47'


class TestClientFactory(ScenarioTest):
    def test_get_mgmt_service_client(self):
        cli = DummyCli()
        client = get_mgmt_service_client(cli, ResourceType.MGMT_RESOURCE_RESOURCES)
        assert client

    def test_get_mgmt_service_client_with_aux_subs_and_tenants(self):
        cli = DummyCli()

        # Specify aux_subscriptions
        client = get_mgmt_service_client(cli, ResourceType.MGMT_RESOURCE_RESOURCES,
                                         aux_subscriptions=[AUX_SUBSCRIPTION])

        assert client._config.headers_policy.headers.get('x-ms-authorization-auxiliary')
        assert client._config.headers_policy.headers.get('x-ms-authorization-auxiliary').startswith("Bearer ")

        # Specify aux_tenants
        client = get_mgmt_service_client(cli, ResourceType.MGMT_RESOURCE_RESOURCES,
                                         aux_tenants=[AUX_TENANT])

        assert client._config.headers_policy.headers.get('x-ms-authorization-auxiliary')
        assert client._config.headers_policy.headers.get('x-ms-authorization-auxiliary').startswith("Bearer ")

        # But not both
        with self.assertRaisesRegex(CLIError, "only one of aux_subscriptions and aux_tenants"):
            client = get_mgmt_service_client(cli, ResourceType.MGMT_RESOURCE_RESOURCES,
                                             aux_subscriptions=[AUX_SUBSCRIPTION],
                                             aux_tenants=[AUX_TENANT])


if __name__ == '__main__':
    unittest.main()
