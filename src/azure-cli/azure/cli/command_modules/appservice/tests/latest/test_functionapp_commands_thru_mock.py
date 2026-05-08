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
    enable_zip_deploy_flex,
    add_remote_build_app_settings,
    remove_remote_build_app_settings,
    config_source_control,
    validate_app_settings_in_scm,
    update_container_settings_functionapp,
    create_functionapp)
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


def _get_zip_deploy_headers(username, password, cmd_mock_client):
    from urllib3.util import make_headers
    from azure.cli.core.util import get_az_user_agent

    headers = make_headers(basic_auth='{0}:{1}'.format(username, password))
    headers['Content-Type'] = 'application/octet-stream'
    headers['Cache-Control'] = 'no-cache'
    headers['User-Agent'] = get_az_user_agent()
    headers['x-ms-client-request-id'] = cmd_mock_client.data['headers']['x-ms-client-request-id']
    return headers


def _get_flex_zip_deploy_headers(cmd_mock_client):
    from urllib3.util import make_headers
    from azure.cli.core.util import get_az_user_agent

    headers = make_headers()
    headers['Authorization'] = "Bearer 1234"
    headers['Content-Type'] = 'application/zip'
    headers['Cache-Control'] = 'no-cache'
    headers['User-Agent'] = get_az_user_agent()
    headers['x-ms-client-request-id'] = cmd_mock_client.data['headers']['x-ms-client-request-id']
    return headers


class TestFunctionappMocked(unittest.TestCase):
    def setUp(self):
        self.client = WebSiteManagementClient(mock.MagicMock(), '123455678')

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_flex_functionapp', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom.enable_zip_deploy')
    @mock.patch('azure.cli.command_modules.appservice.custom.add_remote_build_app_settings')
    def test_functionapp_zip_deploy_flow(self,
                                         add_remote_build_app_settings_mock,
                                         enable_zip_deploy_mock,
                                         is_flex_functionapp_mock,
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
    @mock.patch('azure.cli.command_modules.appservice.custom.is_flex_functionapp', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom.enable_zip_deploy')
    @mock.patch('azure.cli.command_modules.appservice.custom.remove_remote_build_app_settings')
    def test_functionapp_zip_deploy_flow(self,
                                         remove_remote_build_app_settings_mock,
                                         enable_zip_deploy_mock,
                                         is_flex_functionapp_mock,
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

    @mock.patch('azure.cli.command_modules.appservice.custom.check_language_runtime')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.validate_zip_deploy_app_setting_exists')
    @mock.patch('azure.cli.command_modules.appservice.custom.upload_zip_to_storage')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_plan_consumption', return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.is_flex_functionapp', return_value=False)
    def test_functionapp_linux_consumption_non_remote_build(self,
                                                            is_flex_functionapp_mock,
                                                            is_plan_consumption_mock,
                                                            upload_zip_to_storage_mock,
                                                            validate_zip_deploy_app_setting_exists_mock,
                                                            parse_resource_id_mock,
                                                            web_client_factory_mock,
                                                            check_language_runtime_mock):
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

    @mock.patch('azure.cli.command_modules.appservice.custom.check_language_runtime')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.validate_zip_deploy_app_setting_exists')
    @mock.patch('azure.cli.command_modules.appservice.custom.upload_zip_to_storage')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_plan_consumption', return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.is_flex_functionapp', return_value=False)
    def test_functionapp_linux_consumption_non_remote_build_with_slot(self,
                                                            is_flex_functionapp_mock,
                                                            is_plan_consumption_mock,
                                                            upload_zip_to_storage_mock,
                                                            validate_zip_deploy_app_setting_exists_mock,
                                                            parse_resource_id_mock,
                                                            web_client_factory_mock,
                                                            check_language_runtime_mock):
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
        enable_zip_deploy_functionapp(cmd_mock, 'rg', 'name', 'src', build_remote=False, timeout=None, slot='slot')

        # assert
        web_client_mock.web_apps.get.assert_called_with('rg', 'name')
        upload_zip_to_storage_mock.assert_called_with(cmd_mock, 'rg', 'name', 'src', 'slot')

    @mock.patch('azure.cli.command_modules.appservice.custom.check_language_runtime')
    @mock.patch('azure.cli.command_modules.appservice.custom.add_remote_build_app_settings')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_flex_functionapp', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom.enable_zip_deploy')
    def test_functionapp_remote_build_supports_linux(self,
                                                     enable_zip_deploy_mock,
                                                     is_flex_functionapp_mock,
                                                     parse_resource_id_mock,
                                                     web_client_factory_mock,
                                                     add_remote_build_app_settings_mock,
                                                     check_language_runtime_mock):
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

    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', return_value='https://mock-scm')
    @mock.patch('azure.cli.command_modules.appservice.custom.get_runtime_config')
    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers_flex')
    @mock.patch('requests.post', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._check_zip_deployment_status_flex')
    def test_enable_zip_deploy_flex(self,
                                    check_zip_deployment_status_mock,
                                    requests_post_mock,
                                    get_scm_site_headers_flex_mock,
                                    get_runtime_config_mock,
                                    get_scm_url_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        response = mock.MagicMock()
        response.status_code = 202
        requests_post_mock.return_value = response

        get_runtime_config_mock.return_value = {
            "name": "java",
        }

        expected_zip_deploy_headers = _get_flex_zip_deploy_headers(cmd_mock.cli_ctx)
        get_scm_site_headers_flex_mock.return_value = expected_zip_deploy_headers

        # action
        with mock.patch('builtins.open', new_callable=mock.mock_open, read_data='zip-content'):
            enable_zip_deploy_flex(cmd_mock, 'rg', 'name', 'src', slot=None, build_remote=True)

        # assert
        requests_post_mock.assert_called_with('https://mock-scm/api/publish?RemoteBuild=True&Deployer=az_cli', data='zip-content',
                                              headers=expected_zip_deploy_headers, verify=mock.ANY)
        # TODO improve authorization matcher
        check_zip_deployment_status_mock.assert_called_with(cmd_mock, 'rg', 'name',
                                                            'https://mock-scm/api/deployments/latest', None)


    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', side_effect=ValueError())
    def test_enable_zip_deploy_remote_build_no_scm_site(self,
                                                        get_scm_url_mock,
                                                        get_scm_headers_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        # action
        # When the function app is created before 8/1/2019, it cannot use remote build
        with self.assertRaises(CLIError):
            enable_zip_deploy(cmd_mock, 'rg', 'name', 'src', slot=None)

        # assert
        get_scm_url_mock.assert_called_with(cmd_mock, 'rg', 'name', None)

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', return_value='https://mock-scm')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('requests.post', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._check_zip_deployment_status')
    def test_enable_zip_deploy_accepted(self,
                                        check_zip_deployment_status_mock,
                                        requests_post_mock,
                                        web_client_factory_mock,
                                        get_scm_url_mock,
                                        get_scm_headers_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        response = mock.MagicMock()
        response.status_code = 202
        requests_post_mock.return_value = response

        appservice_mock = mock.Mock()
        appservice_mock.kind = "functionapp"

        web_client_mock = mock.Mock()
        web_client_mock.web_apps = mock.Mock()
        web_client_mock.web_apps.get = mock.Mock(return_value=appservice_mock)
        web_client_factory_mock.return_value = web_client_mock

        expected_zip_deploy_headers = _get_zip_deploy_headers('usr', 'pwd', cmd_mock.cli_ctx)
        get_scm_headers_mock.return_value = expected_zip_deploy_headers

        # action
        with mock.patch('builtins.open', new_callable=mock.mock_open, read_data='zip-content'):
            enable_zip_deploy(cmd_mock, 'rg', 'name', 'src', slot=None)

        # assert
        requests_post_mock.assert_called_with('https://mock-scm/api/zipdeploy?isAsync=true&Deployer=az_cli_functions', data='zip-content',
                                              headers=expected_zip_deploy_headers, verify=mock.ANY)
        # TODO improve authorization matcher
        check_zip_deployment_status_mock.assert_called_with(cmd_mock, 'rg', 'name',
                                                            'https://mock-scm/api/deployments/latest', mock.ANY, None)

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', return_value='https://mock-scm')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('requests.post', autospec=True)
    def test_enable_zip_deploy_conflict(self,
                                        requests_post_mock,
                                        web_client_factory_mock,
                                        get_scm_url_mock,
                                        get_scm_headers_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        response = mock.MagicMock()
        response.status_code = 409
        requests_post_mock.return_value = response

        appservice_mock = mock.Mock()
        appservice_mock.kind = "functionapp"

        web_client_mock = mock.Mock()
        web_client_mock.web_apps = mock.Mock()
        web_client_mock.web_apps.get = mock.Mock(return_value=appservice_mock)
        web_client_factory_mock.return_value = web_client_mock

        expected_zip_deploy_headers = _get_zip_deploy_headers('usr', 'pwd', cmd_mock.cli_ctx)
        get_scm_headers_mock.return_value = expected_zip_deploy_headers

        # action
        with mock.patch('builtins.open', new_callable=mock.mock_open, read_data='zip-content'):
            with self.assertRaises(UnclassifiedUserFault):
                enable_zip_deploy(cmd_mock, 'rg', 'name', 'src', slot=None)

        # assert
        requests_post_mock.assert_called_with('https://mock-scm/api/zipdeploy?isAsync=true&Deployer=az_cli_functions', data='zip-content',
                                              headers=expected_zip_deploy_headers, verify=mock.ANY)

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', return_value='https://mock-scm')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('requests.post', autospec=True)
    def test_enable_zip_deploy_service_unavailable(self,
                                                   requests_post_mock,
                                                   web_client_factory_mock,
                                                   get_scm_url_mock,
                                                   get_scm_headers_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        response = mock.MagicMock()
        response.status_code = 503
        requests_post_mock.return_value = response

        appservice_mock = mock.Mock()
        appservice_mock.kind = "functionapp"

        web_client_mock = mock.Mock()
        web_client_mock.web_apps = mock.Mock()
        web_client_mock.web_apps.get = mock.Mock(return_value=appservice_mock)
        web_client_factory_mock.return_value = web_client_mock


        expected_zip_deploy_headers = _get_zip_deploy_headers('usr', 'pwd', cmd_mock.cli_ctx)
        get_scm_headers_mock.return_value = expected_zip_deploy_headers

        # action
        with mock.patch('builtins.open', new_callable=mock.mock_open, read_data='zip-content'):
            with self.assertRaises(AzureInternalError):
                enable_zip_deploy(cmd_mock, 'rg', 'name', 'src', slot=None)

        # assert
        requests_post_mock.assert_called_with('https://mock-scm/api/zipdeploy?isAsync=true&Deployer=az_cli_functions', data='zip-content',
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

    @mock.patch('azure.cli.command_modules.appservice.custom.check_language_runtime')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_centauri_functionapp')
    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    @mock.patch('azure.cli.command_modules.appservice.custom.update_functionapp_polling', return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.update_container_settings', autospec=True)
    def test_update_container_settings_functionapp(self,
                                                   update_container_settings_mock,
                                                   update_functionapp_polling_mock,
                                                   site_op_mock,
                                                   is_centauri_functionapp_mock,
                                                   check_language_runtime_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        Site, DaprConfig, ResourceConfig = cmd_mock.get_models('Site', 'DaprConfig', 'ResourceConfig')
        site = Site(dapr_config=None, location='westus', name='name', resource_config=ResourceConfig())
        site_op_mock.return_value = site
        
        is_centauri_functionapp_mock.return_value = True

        check_language_runtime_mock.return_value = True

        # action
        update_container_settings_functionapp(cmd_mock, 'rg', 'name', workload_profile_name='d4', cpu=0.5, memory='1Gi')

        # assert
        updated_site = site
        updated_site.dapr_config = DaprConfig()
        update_functionapp_polling_mock.assert_called_with(cmd_mock, 'rg', 'name', updated_site)


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


    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._get_location_from_webapp')
    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.LongRunningOperation.__call__', autospec=True)
    def test_config_source_control(self,
                                   long_running_operation_mock,
                                   site_op_mock,
                                   location_mock,
                                   web_client_factory_mock):
        # prepare
        client = mock.Mock()
        web_client_factory_mock.return_value = client

        location_mock.return_value = mock.MagicMock()

        site_op_mock.return_value = mock.MagicMock()

        cmd_mock = _get_test_cmd()

        SiteSourceControl, GitHubActionConfiguration, GitHubActionContainerConfiguration = cmd_mock.get_models('SiteSourceControl', 'GitHubActionConfiguration', 'GitHubActionContainerConfiguration')
        container_config = GitHubActionContainerConfiguration(username="username", password="password")
        github_action_config = GitHubActionConfiguration(container_configuration=container_config)
        source_control = SiteSourceControl(git_hub_action_configuration=github_action_config)

        long_running_operation_mock.return_value = source_control

        # action
        response = config_source_control(cmd_mock, 'rg', 'functionapp', 'https://github.com/yugang/azure-site-test')

        # assert
        self.assertEqual(response.git_hub_action_configuration.container_configuration.password, None)


class TestCreateFunctionAppFlexProviderRegistration(unittest.TestCase):
    def _setup_flex_runtime_mock(self, flex_runtime_helper_mock):
        flex_sku = {
            'functionAppConfigProperties': {
                'runtime': {'name': 'python', 'version': '3.11'}
            },
            'instanceMemoryMB': [{'size': 2048, 'isDefault': True}],
            'maximumInstanceCount': {'defaultValue': 100}
        }
        matched_runtime = mock.MagicMock()
        matched_runtime.sku = flex_sku
        matched_runtime.app_insights = False
        flex_runtime_helper_mock.return_value.resolve.return_value = matched_runtime

    def _setup_deployment_storage_mock(self, validate_deployment_storage_mock, get_deployment_container_mock):
        deployment_storage = mock.MagicMock()
        deployment_storage.primary_endpoints.blob = 'https://storage.blob.core.windows.net/'
        validate_deployment_storage_mock.return_value = deployment_storage
        container = mock.MagicMock()
        container.name = 'container'
        get_deployment_container_mock.return_value = container

    def _setup_client_mock(self, web_client_factory_mock):
        client = mock.MagicMock()
        functionapp_result = mock.MagicMock()
        functionapp_result.resource_group = 'rg'
        functionapp_result.name = 'name'
        web_client_factory_mock.return_value = client
        return client, functionapp_result

    @mock.patch('azure.cli.command_modules.appservice.custom.get_raw_functionapp')
    @mock.patch('azure.cli.command_modules.appservice.custom._set_remote_or_local_git')
    @mock.patch('azure.cli.command_modules.appservice.custom.LongRunningOperation')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_storage_connection_string', return_value='conn_str')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_or_create_deployment_storage_container')
    @mock.patch('azure.cli.command_modules.appservice.custom._validate_and_get_deployment_storage')
    @mock.patch('azure.cli.command_modules.appservice.custom.create_flex_app_service_plan')
    @mock.patch('azure.cli.command_modules.appservice.custom.register_app_provider')
    @mock.patch('azure.cli.command_modules.appservice.custom._validate_and_get_connection_string', return_value='conn_str')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_storage_account_network_restricted', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom._FlexFunctionAppStackRuntimeHelper')
    @mock.patch('azure.cli.command_modules.appservice.custom.list_flexconsumption_locations',
                return_value=[{'name': 'northeurope'}])
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_create_functionapp_flex_registers_app_provider(
            self, web_client_factory_mock, list_flex_locations_mock, flex_runtime_helper_mock,
            is_storage_restricted_mock, validate_conn_string_mock, register_app_provider_mock,
            create_flex_plan_mock, validate_deployment_storage_mock, get_deployment_container_mock,
            get_storage_conn_string_mock, long_running_op_mock, set_remote_git_mock, get_raw_functionapp_mock):
        cmd_mock = _get_test_cmd()
        client, functionapp_result = self._setup_client_mock(web_client_factory_mock)
        self._setup_flex_runtime_mock(flex_runtime_helper_mock)
        self._setup_deployment_storage_mock(validate_deployment_storage_mock, get_deployment_container_mock)
        create_flex_plan_mock.return_value = mock.MagicMock(id='/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan')
        long_running_op_mock.return_value = mock.MagicMock(return_value=functionapp_result)

        # action
        create_functionapp(cmd_mock, 'rg', 'name', 'storage',
                           flexconsumption_location='northeurope', runtime='python')

        # assert register_app_provider is called when flexconsumption_location is used
        register_app_provider_mock.assert_called_once_with(cmd_mock)

    @mock.patch('azure.cli.command_modules.appservice.custom.get_raw_functionapp')
    @mock.patch('azure.cli.command_modules.appservice.custom._set_remote_or_local_git')
    @mock.patch('azure.cli.command_modules.appservice.custom.LongRunningOperation')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_storage_connection_string', return_value='conn_str')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_or_create_deployment_storage_container')
    @mock.patch('azure.cli.command_modules.appservice.custom._validate_and_get_deployment_storage')
    @mock.patch('azure.cli.command_modules.appservice.custom.create_flex_app_service_plan')
    @mock.patch('azure.cli.command_modules.appservice.custom.register_app_provider')
    @mock.patch('azure.cli.command_modules.appservice.custom._validate_and_get_connection_string', return_value='conn_str')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_storage_account_network_restricted', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom._FlexFunctionAppStackRuntimeHelper')
    @mock.patch('azure.cli.command_modules.appservice.custom.list_flexconsumption_locations',
                return_value=[{'name': 'northeurope'}])
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_create_functionapp_flex_registers_app_provider_with_vnet(
            self, web_client_factory_mock, list_flex_locations_mock, flex_runtime_helper_mock,
            is_storage_restricted_mock, validate_conn_string_mock, register_app_provider_mock,
            create_flex_plan_mock, validate_deployment_storage_mock, get_deployment_container_mock,
            get_storage_conn_string_mock, long_running_op_mock, set_remote_git_mock, get_raw_functionapp_mock):
        cmd_mock = _get_test_cmd()
        client, functionapp_result = self._setup_client_mock(web_client_factory_mock)
        self._setup_flex_runtime_mock(flex_runtime_helper_mock)
        self._setup_deployment_storage_mock(validate_deployment_storage_mock, get_deployment_container_mock)
        create_flex_plan_mock.return_value = mock.MagicMock(id='/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan')
        long_running_op_mock.return_value = mock.MagicMock(return_value=functionapp_result)

        with mock.patch('azure.cli.command_modules.appservice.custom._get_subnet_info') as get_subnet_info_mock, \
             mock.patch('azure.cli.command_modules.appservice.custom._validate_vnet_integration_location'), \
             mock.patch('azure.cli.command_modules.appservice.custom._vnet_delegation_check'):
            get_subnet_info_mock.return_value = {
                'resource_group_name': 'rg',
                'vnet_name': 'vnet',
                'subnet_name': 'subnet',
                'subnet_subscription_id': 'sub',
                'subnet_resource_id': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet/subnets/subnet'
            }
            # action
            create_functionapp(cmd_mock, 'rg', 'name', 'storage',
                               flexconsumption_location='northeurope', runtime='python',
                               vnet='vnet', subnet='subnet')

        # assert register_app_provider is called when flexconsumption_location is used with vnet
        register_app_provider_mock.assert_called_with(cmd_mock)

    @mock.patch('azure.cli.command_modules.appservice.custom._set_remote_or_local_git')
    @mock.patch('azure.cli.command_modules.appservice.custom.LongRunningOperation')
    @mock.patch('azure.cli.command_modules.appservice.custom.register_app_provider')
    @mock.patch('azure.cli.command_modules.appservice.custom._validate_and_get_connection_string', return_value='conn_str')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_storage_account_network_restricted', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom._FunctionAppStackRuntimeHelper')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_create_functionapp_flex_plan_registers_app_provider(
            self, web_client_factory_mock, func_runtime_helper_mock, is_storage_restricted_mock,
            validate_conn_string_mock, register_app_provider_mock, long_running_op_mock, set_remote_git_mock):
        cmd_mock = _get_test_cmd()
        client, functionapp_result = self._setup_client_mock(web_client_factory_mock)

        flex_plan = mock.MagicMock()
        flex_plan.location = 'northeurope'
        flex_plan.reserved = True
        flex_plan.sku.tier = 'FlexConsumption'
        client.app_service_plans.get.return_value = flex_plan

        matched_runtime = mock.MagicMock()
        matched_runtime.app_insights = False
        matched_runtime.site_config_dict.as_dict.return_value = {}
        matched_runtime.site_config_dict.additional_properties = {}
        matched_runtime.app_settings_dict = {}
        func_runtime_helper_mock.return_value.resolve.return_value = matched_runtime

        long_running_op_mock.return_value = mock.MagicMock(return_value=functionapp_result)

        # action
        create_functionapp(cmd_mock, 'rg', 'name', 'storage',
                           plan='myplan', functions_version='4', runtime='python')

        # assert register_app_provider is called when plan has FlexConsumption tier
        register_app_provider_mock.assert_called_once_with(cmd_mock)

    @mock.patch('azure.cli.command_modules.appservice.custom._set_remote_or_local_git')
    @mock.patch('azure.cli.command_modules.appservice.custom.LongRunningOperation')
    @mock.patch('azure.cli.command_modules.appservice.custom.register_app_provider')
    @mock.patch('azure.cli.command_modules.appservice.custom._validate_and_get_connection_string', return_value='conn_str')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_storage_account_network_restricted', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom._FunctionAppStackRuntimeHelper')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_create_functionapp_non_flex_plan_does_not_register_app_provider(
            self, web_client_factory_mock, func_runtime_helper_mock, is_storage_restricted_mock,
            validate_conn_string_mock, register_app_provider_mock, long_running_op_mock, set_remote_git_mock):
        cmd_mock = _get_test_cmd()
        client, functionapp_result = self._setup_client_mock(web_client_factory_mock)

        standard_plan = mock.MagicMock()
        standard_plan.location = 'northeurope'
        standard_plan.reserved = True
        standard_plan.sku.tier = 'Standard'
        client.app_service_plans.get.return_value = standard_plan

        matched_runtime = mock.MagicMock()
        matched_runtime.app_insights = False
        matched_runtime.site_config_dict.as_dict.return_value = {}
        matched_runtime.site_config_dict.additional_properties = {}
        matched_runtime.app_settings_dict = {}
        func_runtime_helper_mock.return_value.resolve.return_value = matched_runtime

        long_running_op_mock.return_value = mock.MagicMock(return_value=functionapp_result)

        # action
        create_functionapp(cmd_mock, 'rg', 'name', 'storage',
                           plan='myplan', functions_version='4', runtime='python')

        # assert register_app_provider is NOT called for non-FlexConsumption plans
        register_app_provider_mock.assert_not_called()

