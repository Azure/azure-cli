# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import mock

from azure.cli.command_modules.appservice.static_sites import *
from azure.mgmt.web.models import StaticSiteARMResource


class TestStaticAppCommands(unittest.TestCase):
    def setUp(self):
        self.mock_logger = mock.MagicMock()
        self.mock_cmd = mock.MagicMock()
        self.mock_cmd.cli_ctx = mock.MagicMock()
        self.staticapp_client = mock.MagicMock()

        patcher = mock.patch('azure.cli.command_modules.appservice.static_sites._get_staticsites_client_factory',
                             autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_static_site_client_factory = patcher.start()
        self.mock_static_site_client_factory.return_value = self.staticapp_client

        from azure.mgmt.web import WebSiteManagementClient
        from azure.cli.core.adal_authentication import AdalAuthentication
        self.client = WebSiteManagementClient(AdalAuthentication(lambda: ('bearer', 'secretToken')), '123455678')


    def test_list_empty_staticapp(self):
        self.staticapp_client.list.return_value = []

        response = list_staticsites(self.mock_cmd)

        self.assertEqual(len(response), 0)


    def test_list_staticapp_without_resourcegroup(self):
        staticapp1 = StaticSiteARMResource(location='westus2')
        staticapp2 = StaticSiteARMResource(location='eastus')
        self.staticapp_client.list.return_value = [staticapp1, staticapp2]

        response = list_staticsites(self.mock_cmd)

        self.assertEqual(len(response), 2)
        self.assertIn(staticapp1, response)
        self.assertIn(staticapp2, response)


    def test_list_staticapp_with_resourcegroup(self):
        rg = 'rg1'
        staticapp1 = StaticSiteARMResource(location='westus2')
        self.staticapp_client.get_static_sites_by_resource_group.return_value = [staticapp1]

        response = list_staticsites(self.mock_cmd, rg)

        self.staticapp_client.get_static_sites_by_resource_group.assert_called_with(rg)
        self.assertEqual(len(response), 1)
        self.assertIn(staticapp1, response)
