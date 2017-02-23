# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import unittest
import mock

from requests import Response

from azure.mgmt.web.models import SourceControl, HostNameBinding, Site
from azure.mgmt.web import WebSiteManagementClient
from azure.cli.core.adal_authentication import AdalAuthentication
from azure.cli.command_modules.appservice.custom import (set_deployment_user,
                                                         update_git_token, add_hostname)

# pylint: disable=line-too-long

class Test_Webapp_Mocked(unittest.TestCase):

    def setUp(self):
        self.client = WebSiteManagementClient(AdalAuthentication(lambda: ('bearer',
                                                                          'secretToken')),
                                              '123455678')

    # pylint: disable=no-self-argument,no-self-use,protected-access,no-member
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_set_deployment_user_creds(self, client_factory_mock):
        self.client._client = mock.MagicMock()
        client_factory_mock.return_value = self.client
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        self.client._client.send.return_value = mock_response

        # action
        result = set_deployment_user('admin', 'verySecret1')

        # assert things get wired up with a result returned
        self.assertIsNotNone(result)

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_set_source_control_token(self, client_factory_mock):
        client_factory_mock.return_value = self.client
        self.client._client = mock.MagicMock()
        sc = SourceControl('not-really-needed', name='GitHub', token='veryNiceToken')
        self.client._client.send.return_value = Test_Webapp_Mocked._make_response(sc.__dict__)

        # action
        result = update_git_token('veryNiceToken')

        # assert things gets wired up
        self.assertEqual(result.token, 'veryNiceToken')

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_set_domain_name(self, client_factory_mock):
        client_factory_mock.return_value = self.client
        # set up the return value for getting a webapp
        webapp = Site('westus')
        webapp.name = 'veryNiceWebApp'
        self.client.web_apps.get = lambda _, _1: webapp

        # set up the result value of putting a domain name
        domain = 'veryNiceDomain'
        binding = HostNameBinding(webapp.location, name=domain,
                                  custom_host_name_dns_record_type='A',
                                  host_name_type='Managed')
        self.client.web_apps._client = mock.MagicMock()
        self.client.web_apps._client.send.return_value = Test_Webapp_Mocked._make_response(binding.__dict__)

        # action
        result = add_hostname('g1', webapp.name, domain)

        # assert
        self.assertEqual(result.name, domain)

    @staticmethod
    def _make_response(content_json):
        resp = mock.create_autospec(Response)
        resp.text = json.dumps(content_json)
        resp.encoding = 'utf-8'
        resp.status_code = 200
        return resp


if __name__ == '__main__':
    unittest.main()
