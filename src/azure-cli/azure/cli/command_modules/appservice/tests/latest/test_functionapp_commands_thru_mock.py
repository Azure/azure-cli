# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock
import os

from azure.mgmt.web import WebSiteManagementClient
from knack.util import CLIError
from azure.cli.command_modules.appservice.custom import (
    enable_zip_deploy_functionapp,
    enable_zip_deploy,
    add_remote_build_app_settings,
    remove_remote_build_app_settings,
    validate_app_settings_in_scm)
from azure.cli.core.profiles import ResourceType
from azure.cli.core.azclierror import (AzureInternalError, UnclassifiedUserFault)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


def _get_test_cmd():
    from azure.cli.core.mock import DummyCli
    from azure.cli.core import AzCommandsLoader
    from azure.cli.core.commands import AzCliCommand
    cli_ctx = DummyCli()
    loader = AzCommandsLoader(cli_ctx, resource_type=ResourceType.MGMT_APPSERVICE)
    cmd = AzCliCommand(loader, 'test', None)
    cmd.command_kwargs = {'resource_type': ResourceType.MGMT_APPSERVICE}
    cmd.cli_ctx = cli_ctx
    return cmd


def _get_zip_deploy_headers(username, password):
    from urllib3.util import make_headers
    from azure.cli.core.util import get_az_user_agent

    headers = make_headers(basic_auth='{0}:{1}'.format(username, password))
    headers['Content-Type'] = 'application/octet-stream'
    headers['Cache-Control'] = 'no-cache'
    headers['User-Agent'] = get_az_user_agent()
    return headers


class TestFunctionappMocked(unittest.TestCase):
    def setUp(self):
        self.client = WebSiteManagementClient(mock.MagicMock(), '123455678')

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.enable_zip_deploy')
    @mock.patch('azure.cli.command_modules.appservice.custom.add_remote_build_app_settings')
    def test_functionapp_zip_deploy_flow(self,
                                         add_remote_build_app_settings_mock,
                                         enable_zip_deploy_mock,
                                         parse_resource_id_mock,
                                         web_client_factory_mock):
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        # action
        enable_zip_deploy_functionapp(cmd_mock, 'rg', 'name', 'src', build_remote=True, timeout=None, slot=None)

        # assert
        parse_resource_id_mock.assert_called_once()
        enable_zip_deploy_mock.assert_called_once()
        add_remote_build_app_settings_mock.assert_called_once()

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.enable_zip_deploy')
    @mock.patch('azure.cli.command_modules.appservice.custom.remove_remote_build_app_settings')
    def test_functionapp_zip_deploy_flow(self,
                                         remove_remote_build_app_settings_mock,
                                         enable_zip_deploy_mock,
                                         parse_resource_id_mock,
                                         web_client_factory_mock):
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        # action
        enable_zip_deploy_functionapp(cmd_mock, 'rg', 'name', 'src', build_remote=False, timeout=None, slot=None)

        # assert
        parse_resource_id_mock.assert_called_once()
        enable_zip_deploy_mock.assert_called_once()
        remove_remote_build_app_settings_mock.assert_called_once()

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
        cmd_mock = _get_test_cmd()
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

    @mock.patch('azure.cli.command_modules.appservice.custom.add_remote_build_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.enable_zip_deploy')
    def test_functionapp_remote_build_supports_linux(self,
                                                     enable_zip_deploy_mock,
                                                     parse_resource_id_mock,
                                                     web_client_factory_mock,
                                                     add_remote_build_app_settings_mock):
        # prepare
        cmd_mock = _get_test_cmd()
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
        enable_zip_deploy_mock.assert_called_with(cmd_mock, 'rg', 'name', 'src', None, None)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_site_credential', return_value=('usr', 'pwd'))
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', side_effect=ValueError())
    def test_enable_zip_deploy_remote_build_no_scm_site(self,
                                                        get_scm_url_mock,
                                                        get_site_credential_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        # action
        # When the function app is created before 8/1/2019, it cannot use remote build
        with self.assertRaises(CLIError):
            enable_zip_deploy(cmd_mock, 'rg', 'name', 'src', slot=None)

        # assert
        get_site_credential_mock.assert_called_with(cmd_mock.cli_ctx, 'rg', 'name', None)
        get_scm_url_mock.assert_called_with(cmd_mock, 'rg', 'name', None)
    
    @mock.patch('azure.cli.command_modules.appservice.custom._get_site_credential', return_value=('usr', 'pwd'))
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', return_value='https://mock-scm')
    @mock.patch('requests.post', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._check_zip_deployment_status')
    def test_enable_zip_deploy_accepted(self,
                                        check_zip_deployment_status_mock,
                                        requests_post_mock,
                                        get_scm_url_mock,
                                        get_site_credential_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        response = mock.MagicMock()
        response.status_code = 202
        requests_post_mock.return_value = response

        expected_zip_deploy_headers = _get_zip_deploy_headers('usr', 'pwd')

        # action
        with mock.patch('builtins.open', new_callable=mock.mock_open, read_data='zip-content'):
            enable_zip_deploy(cmd_mock, 'rg', 'name', 'src', slot=None)

        # assert
        requests_post_mock.assert_called_with('https://mock-scm/api/zipdeploy?isAsync=true', data='zip-content',
                                              headers=expected_zip_deploy_headers, verify=mock.ANY)
        # TODO improve authorization matcher
        check_zip_deployment_status_mock.assert_called_with(cmd_mock, 'rg', 'name',
                                                            'https://mock-scm/api/deployments/latest', mock.ANY, None)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_site_credential', return_value=('usr', 'pwd'))
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', return_value='https://mock-scm')
    @mock.patch('requests.post', autospec=True)
    def test_enable_zip_deploy_conflict(self,
                                        requests_post_mock,
                                        get_scm_url_mock,
                                        get_site_credential_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        response = mock.MagicMock()
        response.status_code = 409
        requests_post_mock.return_value = response

        expected_zip_deploy_headers = _get_zip_deploy_headers('usr', 'pwd')

        # action
        with mock.patch('builtins.open', new_callable=mock.mock_open, read_data='zip-content'):
            with self.assertRaises(UnclassifiedUserFault):
                enable_zip_deploy(cmd_mock, 'rg', 'name', 'src', slot=None)

        # assert
        requests_post_mock.assert_called_with('https://mock-scm/api/zipdeploy?isAsync=true', data='zip-content',
                                              headers=expected_zip_deploy_headers, verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_site_credential', return_value=('usr', 'pwd'))
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', return_value='https://mock-scm')
    @mock.patch('requests.post', autospec=True)
    def test_enable_zip_deploy_service_unavailable(self,
                                                   requests_post_mock,
                                                   get_scm_url_mock,
                                                   get_site_credential_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        response = mock.MagicMock()
        response.status_code = 503
        requests_post_mock.return_value = response

        expected_zip_deploy_headers = _get_zip_deploy_headers('usr', 'pwd')

        # action
        with mock.patch('builtins.open', new_callable=mock.mock_open, read_data='zip-content'):
            with self.assertRaises(AzureInternalError):
                enable_zip_deploy(cmd_mock, 'rg', 'name', 'src', slot=None)

        # assert
        requests_post_mock.assert_called_with('https://mock-scm/api/zipdeploy?isAsync=true', data='zip-content',
                                              headers=expected_zip_deploy_headers, verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_app_settings_from_scm', return_value={
        'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true'
    })
    def test_validate_app_settings_in_scm_should_have(self, get_app_settings_from_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        should_have = ['SCM_DO_BUILD_DURING_DEPLOYMENT']

        # action
        result = validate_app_settings_in_scm(cmd_mock, 'rg', 'name', slot=None, should_have=should_have)

        # assert
        self.assertTrue(result)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_app_settings_from_scm', return_value={
        'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true'
    })
    def test_validate_app_settings_in_scm_should_not_have(self, get_app_settings_from_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        should_not_have = ['ENABLE_ORYX_BUILD']

        # action
        result = validate_app_settings_in_scm(cmd_mock, 'rg', 'name', slot=None, should_not_have=should_not_have)

        # assert
        self.assertTrue(result)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_app_settings_from_scm', return_value={
        'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true'
    })
    def test_validate_app_settings_in_scm_should_contain(self, get_app_settings_from_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        should_contain = {'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true'}

        # action
        result = validate_app_settings_in_scm(cmd_mock, 'rg', 'name', slot=None, should_contain=should_contain)

        # assert
        self.assertTrue(result)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_app_settings_from_scm', return_value={
        'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true'
    })
    def test_validate_app_settings_in_scm_should_have_failure(self, get_app_settings_from_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        should_have = ['ENABLE_ORYX_BUILD']

        # action
        result = validate_app_settings_in_scm(cmd_mock, 'rg', 'name', slot=None, should_have=should_have)

        # assert
        self.assertFalse(result)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_app_settings_from_scm', return_value={
        'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true'
    })
    def test_validate_app_Settings_in_scm_should_not_have_failure(self, get_app_settings_from_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        should_not_have = ['SCM_DO_BUILD_DURING_DEPLOYMENT']

        # action
        result = validate_app_settings_in_scm(cmd_mock, 'rg', 'name', slot=None, should_not_have=should_not_have)

        # assert
        self.assertFalse(result)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_app_settings_from_scm', return_value={
        'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true'
    })
    def test_validate_app_settings_in_scm_should_contain_failure(self, get_app_settings_from_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        should_contain = {'SCM_DO_BUILD_DURING_DEPLOYMENT': 'false'}

        # action
        result = validate_app_settings_in_scm(cmd_mock, 'rg', 'name', slot=None, should_contain=should_contain)

        # assert
        self.assertFalse(result)

    @mock.patch('azure.cli.command_modules.appservice.custom.validate_app_settings_in_scm', return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.update_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.delete_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.get_app_settings', return_value=[])
    def test_add_remote_build_app_settings_add_scm_do_build_during_deployment(self,
                                                                              get_app_settings_mock,
                                                                              delete_app_settings_mock,
                                                                              update_app_settings_mock,
                                                                              validate_app_settings_in_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()

        # action
        add_remote_build_app_settings(cmd_mock, 'rg', 'name', slot=None)

        # assert
        update_app_settings_mock.assert_called_with(cmd_mock, 'rg', 'name', ['SCM_DO_BUILD_DURING_DEPLOYMENT=true'], None)
        validate_app_settings_in_scm_mock.assert_called_with(cmd_mock, 'rg', 'name', None,
                                                             should_contain={'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true'},
                                                             should_not_have=[])

    @mock.patch('azure.cli.command_modules.appservice.custom.validate_app_settings_in_scm',
                return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.update_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.delete_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.get_app_settings', return_value=[
        {
            'name': 'WEBSITE_RUN_FROM_PACKAGE',
            'value': 'https://microsoft.com'
        },
        {
            'name': 'ENABLE_ORYX_BUILD',
            'value': 'true'
        }
    ])
    def test_add_remote_build_app_settings_remove_unnecessary_app_settings(self,
                                                                           get_app_settings_mock,
                                                                           delete_app_settings_mock,
                                                                           update_app_settings_mock,
                                                                           validate_app_settings_in_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()

        # action
        add_remote_build_app_settings(cmd_mock, 'rg', 'name', slot=None)

        # assert
        delete_app_settings_mock.assert_any_call(cmd_mock, 'rg', 'name', ['WEBSITE_RUN_FROM_PACKAGE'], None)
        delete_app_settings_mock.assert_any_call(cmd_mock, 'rg', 'name', ['ENABLE_ORYX_BUILD'], None)
        validate_app_settings_in_scm_mock.assert_called_with(cmd_mock, 'rg', 'name', None,
                                                             should_contain={'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true'},
                                                             should_not_have=['WEBSITE_RUN_FROM_PACKAGE', 'ENABLE_ORYX_BUILD'])

    @mock.patch('azure.cli.command_modules.appservice.custom.validate_app_settings_in_scm', return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.update_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.delete_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.get_app_settings', return_value=[{
        'name': 'SCM_DO_BUILD_DURING_DEPLOYMENT',
        'value': 'false'
    }])
    def test_add_remote_build_app_settings_change_scm_do_build_during_deployment(self,
                                                                                 get_app_settings_mock,
                                                                                 delete_app_settings_mock,
                                                                                 update_app_settings_mock,
                                                                                 validate_app_settings_in_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()

        # action
        add_remote_build_app_settings(cmd_mock, 'rg', 'name', slot=None)

        # assert
        update_app_settings_mock.assert_called_with(cmd_mock, 'rg', 'name', ['SCM_DO_BUILD_DURING_DEPLOYMENT=true'], None)
        validate_app_settings_in_scm_mock.assert_called_with(cmd_mock, 'rg', 'name', None,
                                                             should_contain={'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true'},
                                                             should_not_have=[])

    @mock.patch('azure.cli.command_modules.appservice.custom.validate_app_settings_in_scm', return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.update_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.delete_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.get_app_settings', return_value=[{
        'name': 'SCM_DO_BUILD_DURING_DEPLOYMENT',
        'value': 'true'
    }])
    def test_add_remote_build_app_settings_do_nothing(self,
                                                      get_app_settings_mock,
                                                      delete_app_settings_mock,
                                                      update_app_settings_mock,
                                                      validate_app_settings_in_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()

        # action
        add_remote_build_app_settings(cmd_mock, 'rg', 'name', slot=None)

        # assert
        update_app_settings_mock.assert_not_called()
        validate_app_settings_in_scm_mock.assert_not_called()

    @mock.patch('azure.cli.command_modules.appservice.custom.validate_app_settings_in_scm', return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.update_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.delete_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.get_app_settings', return_value=[])
    def test_remove_remote_build_app_settings_disable_scm_do_build_during_deployment(self,
                                                                                     get_app_settings_mock,
                                                                                     delete_app_settings_mock,
                                                                                     update_app_settings_mock,
                                                                                     validate_app_settings_in_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()

        # action
        remove_remote_build_app_settings(cmd_mock, 'rg', 'name', slot=None)

        # assert
        update_app_settings_mock.assert_called_with(cmd_mock, 'rg', 'name', ['SCM_DO_BUILD_DURING_DEPLOYMENT=false'], None)
        validate_app_settings_in_scm_mock.assert_called_with(cmd_mock, 'rg', 'name', None,
                                                             should_contain={'SCM_DO_BUILD_DURING_DEPLOYMENT': 'false'})

    @mock.patch('azure.cli.command_modules.appservice.custom.validate_app_settings_in_scm', return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.update_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.delete_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.get_app_settings', return_value=[{
        'name': 'SCM_DO_BUILD_DURING_DEPLOYMENT',
        'value': 'false'
    }])
    def test_remove_remote_build_app_settings_do_nothing(self,
                                                         get_app_settings_mock,
                                                         delete_app_settings_mock,
                                                         update_app_settings_mock,
                                                         validate_app_settings_in_scm_mock):
        # prepare
        cmd_mock = _get_test_cmd()

        # action
        remove_remote_build_app_settings(cmd_mock, 'rg', 'name', slot=None)

        # assert
        update_app_settings_mock.assert_not_called()
        validate_app_settings_in_scm_mock.assert_not_called()
