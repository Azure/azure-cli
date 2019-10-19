# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import mock
import os

from azure.mgmt.web import WebSiteManagementClient
from azure.cli.core.adal_authentication import AdalAuthentication
from knack.util import CLIError
from azure.cli.command_modules.appservice.custom import (
    enable_zip_deploy_functionapp,
    enable_zip_deploy)


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class TestFunctionappMocked(unittest.TestCase):
    def setUp(self):
        self.client = WebSiteManagementClient(AdalAuthentication(lambda: ('bearer', 'secretToken')), '123455678')

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.enable_zip_deploy')
    def test_functionapp_zip_deploy_flow(self,
                                         enable_zip_deploy_mock,
                                         parse_resource_id_mock,
                                         web_client_factory_mock):
        cmd_mock = mock.MagicMock()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        # action
        enable_zip_deploy_functionapp(cmd_mock, 'rg', 'name', 'src', build_remote=True, timeout=None, slot=None)

        # assert
        parse_resource_id_mock.assert_called_once()
        enable_zip_deploy_mock.assert_called_once()

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.upload_zip_to_storage')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_plan_consumption', return_value=True)
    def test_functionapp_linux_consumption_non_remote_build(self,
                                                            is_plan_consumption_mock,
                                                            upload_zip_to_storage_mock,
                                                            parse_resource_id_mock,
                                                            web_client_factory_mock):
        # prepare
        cmd_mock = mock.MagicMock()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        appservice_mock = mock.Mock()
        appservice_mock.reserved = True  # Marked app service as Linux

        web_client_mock = mock.Mock()
        web_client_mock.web_apps = mock.Mock()
        web_client_mock.web_apps.get = mock.Mock(return_value=appservice_mock)
        web_client_factory_mock.return_value = web_client_mock

        # action
        # Linux Consumption app should use update-storage to deploy when not using remote build
        enable_zip_deploy_functionapp(cmd_mock, 'rg', 'name', 'src', build_remote=False, timeout=None, slot=None)

        # assert
        web_client_mock.web_apps.get.assert_called_with('rg', 'name')
        upload_zip_to_storage_mock.assert_called_with(cmd_mock, 'rg', 'name', 'src', None)

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.enable_zip_deploy')
    def test_functionapp_remote_build_supports_linux(self,
                                                     enable_zip_deploy_mock,
                                                     parse_resource_id_mock,
                                                     web_client_factory_mock):
        # prepare
        cmd_mock = mock.MagicMock()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        appservice_mock = mock.Mock()
        appservice_mock.reserved = True  # Marked app service as Linux

        web_client_mock = mock.Mock()
        web_client_mock.web_apps = mock.Mock()
        web_client_mock.web_apps.get = mock.Mock(return_value=appservice_mock)
        web_client_factory_mock.return_value = web_client_mock

        # action
        enable_zip_deploy_functionapp(cmd_mock, 'rg', 'name', 'src', build_remote=True, timeout=None, slot=None)

        # assert
        web_client_mock.web_apps.get.assert_called_with('rg', 'name')
        enable_zip_deploy_mock.assert_called_with(cmd_mock, 'rg', 'name', 'src', True, None, None)

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.enable_zip_deploy')
    def test_functionapp_remote_build_doesnt_support_windows(self,
                                                             enable_zip_deploy_mock,
                                                             parse_resource_id_mock,
                                                             web_client_factory_mock):
        # prepare
        cmd_mock = mock.MagicMock()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        appservice_mock = mock.Mock()
        appservice_mock.reserved = False  # Marked app service as Windows

        web_client_mock = mock.Mock()
        web_client_mock.web_apps = mock.Mock()
        web_client_mock.web_apps.get = mock.Mock(return_value=appservice_mock)
        web_client_factory_mock.return_value = web_client_mock

        # action
        with self.assertRaises(CLIError):
            enable_zip_deploy_functionapp(cmd_mock, 'rg', 'name', 'src', build_remote=True, timeout=None, slot=None)

        # assert
        web_client_mock.web_apps.get.assert_called_with('rg', 'name')

    @mock.patch('azure.cli.command_modules.appservice.custom._get_site_credential', return_value=('usr', 'pwd'))
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', side_effect=ValueError())
    def test_enable_zip_deploy_remote_build_no_scm_site(self,
                                                        get_scm_url_mock,
                                                        get_site_credential_mock):
        # prepare
        cmd_mock = mock.MagicMock()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        # action
        # When the function app is created before 8/1/2019, it cannot use remote build
        with self.assertRaises(CLIError):
            enable_zip_deploy(cmd_mock, 'rg', 'name', 'src', is_remote_build=True, slot=None)

        # assert
        get_site_credential_mock.assert_called_with(cmd_mock.cli_ctx, 'rg', 'name', None)
        get_scm_url_mock.assert_called_with(cmd_mock, 'rg', 'name', None)
