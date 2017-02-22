# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock

from azure.mgmt.web.models import User, SourceControl, HostNameBinding, Site
from azure.cli.command_modules.appservice.custom import (set_deployment_user,
                                                         update_git_token, add_hostname)


class Test_Webapp_Mocked(unittest.TestCase):
    # pylint: disable=no-self-argument,no-self-use
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_set_deployment_user_creds(self, mock_client_factory):
        client = mock.MagicMock()
        mock_client_factory.return_value = client
        set_deployment_user('admin', 'verySecret1')
        user = User('not-really-needed', publishing_user_name='admin',
                    publishing_password='verySecret1')
        client.update_publishing_user.assert_called_once_with(user)

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_set_source_control_token(self, mock_client_factory):
        client = mock.MagicMock()
        mock_client_factory.return_value = client
        update_git_token('veryNiceToken')
        sc = SourceControl('not-really-needed', name='GitHub', token='veryNiceToken')
        client.update_source_control.assert_called_once_with('GitHub', sc)

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_set_domain_name(self, mock_client_factory):
        client = mock.MagicMock()
        mock_client_factory.return_value = client
        webapp = Site('westus')
        webapp.name = 'veryNiceWebApp'
        client.web_apps.get.return_value = webapp
        domain = 'veryNiceDomain'
        resource_group_name = 'g1'
        add_hostname(resource_group_name, webapp.name, domain)
        binding = HostNameBinding(webapp.location, host_name_binding_name=domain,
                                  site_name=webapp.name)
        client.web_apps.create_or_update_host_name_binding.assert_called_once_with(
            resource_group_name, webapp.name, domain, binding)

if __name__ == '__main__':
    unittest.main()
