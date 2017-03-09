# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import mock

from msrestazure.azure_exceptions import CloudError
from azure.mgmt.web.models import (SourceControl, HostNameBinding, Site, SiteConfig,
                                   HostNameSslState, SslState)
from azure.mgmt.web import WebSiteManagementClient
from azure.cli.core.adal_authentication import AdalAuthentication
from azure.cli.core._util import CLIError
from azure.cli.command_modules.appservice.custom import (set_deployment_user,
                                                         update_git_token, add_hostname,
                                                         update_site_configs,
                                                         view_in_browser,
                                                         sync_site_repo)

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
        self.client._client.send.return_value = FakedResponse(200)
        self.client._deserialize = mock.MagicMock()
        self.client._deserialize.return_value = sc

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
        self.client.web_apps._client.send.return_value = FakedResponse(200)
        self.client.web_apps._deserialize = mock.MagicMock()
        self.client.web_apps._deserialize.return_value = binding
        # action
        result = add_hostname('g1', webapp.name, domain)

        # assert
        self.assertEqual(result.name, domain)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    def test_update_site_config(self, site_op_mock):
        site_config = SiteConfig('antarctica')
        site_op_mock.side_effect = [site_config, None]
        # action
        update_site_configs('myRG', 'myweb', java_version='1.8')
        # assert
        config_for_set = site_op_mock.call_args_list[1][0][4]
        self.assertEqual(config_for_set.java_version, '1.8')
        # point check some unrelated properties should stay at None
        self.assertEqual(config_for_set.use32_bit_worker_process, None)
        self.assertEqual(config_for_set.java_container, None)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.get_streaming_log', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._open_page_in_browser', autospec=True)
    def test_browse_with_trace(self, webbrowser_mock, log_mock, site_op_mock):
        site = Site('antarctica')
        site.default_host_name = 'haha.com'
        site.host_name_ssl_states = [HostNameSslState('does not matter',
                                                      ssl_state=SslState.ip_based_enabled)]

        site_op_mock.return_value = site
        # action
        view_in_browser('myRG', 'myweb', logs=True)
        # assert
        webbrowser_mock.assert_called_with('https://haha.com')
        log_mock.assert_called_with('myRG', 'myweb', None, None)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    def test_sync_repository_with_error(self, site_op_mock):
        resp = FakedResponse(400)
        setattr(resp, 'text', '{"Message": "nice error"}')
        site_op_mock.side_effect = CloudError(resp, error='error1')
        # action
        with self.assertRaises(CLIError) as ex:
            sync_site_repo('myRG', 'myweb')
        # assert
        self.assertEqual("nice error", str(ex.exception))

class FakedResponse(object):  # pylint: disable=too-few-public-methods
    def __init__(self, status_code):
        self.status_code = status_code


if __name__ == '__main__':
    unittest.main()
