# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import io
import json
import unittest
from contextlib import contextmanager
from unittest import mock
from urllib.parse import parse_qs, urlparse
import os

from azure.mgmt.web import WebSiteManagementClient
from knack.util import CLIError
from azure.cli.command_modules.appservice.custom import (
    enable_zip_deploy_functionapp,
    enable_zip_deploy,
    enable_zip_deploy_flex,
    check_flex_app_after_deployment,
    add_remote_build_app_settings,
    remove_remote_build_app_settings,
    config_source_control,
    validate_app_settings_in_scm,
    update_container_settings_functionapp,
    list_function_keys,
    migrate_consumption_to_flex,
    _upgrade_consumption_to_flex_in_place,
    _build_flex_function_app_config,
    _prepare_flex_deployment_storage,
    _prepare_flex_deployment_storage_identity,
    revert_flex_migration,
    assign_identity,
    create_functionapp,
    delete_always_ready_settings,
    get_deployment_configs,
    remove_identity,
    set_update_strategy_config,
    show_functionapp,
    update_always_ready_settings,
    update_deployment_configs,
    update_runtime_config,
    update_scale_config)
from azure.cli.core.profiles import ResourceType
from azure.cli.core.azclierror import (AzureInternalError, UnclassifiedUserFault, HTTPError)
from azure.cli.core.azclierror import (ResourceNotFoundError, MutuallyExclusiveArgumentError,
                                        RequiredArgumentMissingError, ValidationError, ArgumentUsageError)

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

    @mock.patch('time.sleep')
    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core.util.should_disable_connection_verify', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom.list_host_keys')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_host_url',
                return_value='https://mock-func.azurewebsites.net')
    def test_check_flex_app_after_deployment_success(self,
                                                     get_host_url_mock,
                                                     list_host_keys_mock,
                                                     should_disable_verify_mock,
                                                     requests_get_mock,
                                                     sleep_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        list_host_keys_mock.return_value = mock.Mock(master_key='master-key')
        response = mock.Mock(status_code=200, reason='OK')
        requests_get_mock.return_value = response

        # action
        result = check_flex_app_after_deployment(cmd_mock, 'rg', 'name')

        # assert
        self.assertEqual(result, "Deployment was successful.")
        requests_get_mock.assert_called_with('https://mock-func.azurewebsites.net/admin/host/status',
                                             headers={"x-functions-key": 'master-key'},
                                             verify=True)

    @mock.patch('time.sleep')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_host_url', side_effect=ValueError())
    def test_check_flex_app_after_deployment_host_url_fetch_failure(self,
                                                                    get_host_url_mock,
                                                                    sleep_mock):
        # prepare
        cmd_mock = _get_test_cmd()

        # action
        with self.assertRaises(ResourceNotFoundError):
            check_flex_app_after_deployment(cmd_mock, 'rg', 'name')

        # assert
        get_host_url_mock.assert_called_once_with(cmd_mock, 'rg', 'name')

    @mock.patch('time.sleep')
    @mock.patch('azure.cli.command_modules.appservice.custom.list_host_keys', side_effect=Exception())
    @mock.patch('azure.cli.command_modules.appservice.custom._get_host_url',
                return_value='https://mock-func.azurewebsites.net')
    def test_check_flex_app_after_deployment_host_key_fetch_failure(self,
                                                                    get_host_url_mock,
                                                                    list_host_keys_mock,
                                                                    sleep_mock):
        # prepare
        cmd_mock = _get_test_cmd()

        # action
        with self.assertRaises(ResourceNotFoundError):
            check_flex_app_after_deployment(cmd_mock, 'rg', 'name')

        # assert
        list_host_keys_mock.assert_called_once_with(cmd_mock, 'rg', 'name')

    @mock.patch('time.sleep')
    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core.util.should_disable_connection_verify', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom.list_host_keys')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_host_url',
                return_value='https://mock-func.azurewebsites.net')
    def test_check_flex_app_after_deployment_ip_restriction(self,
                                                            get_host_url_mock,
                                                            list_host_keys_mock,
                                                            should_disable_verify_mock,
                                                            requests_get_mock,
                                                            sleep_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        list_host_keys_mock.return_value = mock.Mock(master_key='master-key')
        requests_get_mock.return_value = mock.Mock(status_code=403, reason='Ip Forbidden')

        # action
        result = check_flex_app_after_deployment(cmd_mock, 'rg', 'name')

        # assert
        self.assertEqual(result, "Deployment was successful but health check failed due to IP restriction.")

    @mock.patch('time.sleep')
    @mock.patch('requests.get', autospec=True)
    @mock.patch('azure.cli.core.util.should_disable_connection_verify', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom.list_host_keys')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_host_url',
                return_value='https://mock-func.azurewebsites.net')
    def test_check_flex_app_after_deployment_unhealthy(self,
                                                       get_host_url_mock,
                                                       list_host_keys_mock,
                                                       should_disable_verify_mock,
                                                       requests_get_mock,
                                                       sleep_mock):
        # prepare
        cmd_mock = _get_test_cmd()
        list_host_keys_mock.return_value = mock.Mock(master_key='master-key')
        requests_get_mock.return_value = mock.Mock(status_code=500, reason='Internal Server Error')

        # action
        with self.assertRaises(CLIError):
            check_flex_app_after_deployment(cmd_mock, 'rg', 'name')

        # assert
        self.assertEqual(requests_get_mock.call_count, 15)


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
    @mock.patch('azure.cli.command_modules.appservice.utils._get_location_from_webapp')
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

    def test_flex_parse_raw_stacks_handles_empty_app_settings_dictionary(self):
        from azure.cli.command_modules.appservice.custom import _FlexFunctionAppStackRuntimeHelper

        # prepare
        cmd_mock = _get_test_cmd()
        go_stack = {
            'name': 'go',
            'properties': {'majorVersions': [{'minorVersions': [{
                'value': '1.0',
                'stackSettings': {'linuxRuntimeSettings': {
                    'appSettingsDictionary': {},
                    'Sku': [{'skuCode': 'FC1'}],
                    'gitHubActionSettings': {'isSupported': True},
                    'appInsightsSettings': {'isSupported': True},
                    'isDefault': True,
                }},
            }]}]},
        }

        # action
        with mock.patch.object(_FlexFunctionAppStackRuntimeHelper,
                               'get_flex_raw_function_app_stacks',
                               return_value=[go_stack]):
            matched = _FlexFunctionAppStackRuntimeHelper(cmd_mock, 'westcentralus', 'go').resolve('go', '1.0')

        # assert
        self.assertEqual(matched.name, 'go')
        self.assertEqual(matched.version, '1.0')

    def test_flex_parse_raw_stacks_prefers_functions_worker_runtime_when_present(self):
        # FUNCTIONS_WORKER_RUNTIME overrides runtime['name'] when set (e.g., dotnet-isolated under the dotnet stack).
        from azure.cli.command_modules.appservice.custom import _FlexFunctionAppStackRuntimeHelper

        # prepare
        cmd_mock = _get_test_cmd()
        dotnet_isolated_stack = {
            'name': 'dotnet',
            'properties': {'majorVersions': [{'minorVersions': [{
                'value': '8.0',
                'stackSettings': {'linuxRuntimeSettings': {
                    'appSettingsDictionary': {'FUNCTIONS_WORKER_RUNTIME': 'dotnet-isolated'},
                    'Sku': [{'skuCode': 'FC1'}],
                    'gitHubActionSettings': {'isSupported': True},
                    'appInsightsSettings': {'isSupported': True},
                    'isDefault': True,
                }},
            }]}]},
        }

        # action
        with mock.patch.object(_FlexFunctionAppStackRuntimeHelper,
                               'get_flex_raw_function_app_stacks',
                               return_value=[dotnet_isolated_stack]):
            matched = _FlexFunctionAppStackRuntimeHelper(
                cmd_mock, 'westcentralus', 'dotnet-isolated').resolve('dotnet-isolated', '8.0')

        # assert
        self.assertEqual(matched.name, 'dotnet-isolated')

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_list_function_keys_unwraps_broken_string_dictionary(self, web_client_factory_mock):
        # azure-mgmt-web 11.0.0 deserializes flat dictionary responses with .properties = None
        from azure.mgmt.web import models as _models
        from azure.mgmt.web._utils.model_base import _deserialize

        broken = _deserialize(
            _models.StringDictionary,
            {'default': 'vvrX4LJY1JWbimFI28UM', 'myCustomKey': 'abc'})
        self.assertIsNone(broken.properties)

        cmd_mock = _get_test_cmd()
        client_mock = mock.MagicMock()
        client_mock.web_apps.list_function_keys.return_value = broken
        web_client_factory_mock.return_value = client_mock

        result = list_function_keys(cmd_mock, 'rg', 'app', 'httpget')

        self.assertEqual(result, {'default': 'vvrX4LJY1JWbimFI28UM', 'myCustomKey': 'abc'})
        client_mock.web_apps.list_function_keys.assert_called_once_with('rg', 'app', 'httpget')
        client_mock.web_apps.list_function_keys_slot.assert_not_called()

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_list_function_keys_uses_properties_when_sdk_returns_enveloped_response(self, web_client_factory_mock):
        # Prefers .properties when populated (forward-compatible with a future SDK fix)
        fixed = mock.MagicMock()
        fixed.properties = {'default': 'abc'}

        cmd_mock = _get_test_cmd()
        client_mock = mock.MagicMock()
        client_mock.web_apps.list_function_keys_slot.return_value = fixed
        web_client_factory_mock.return_value = client_mock

        result = list_function_keys(cmd_mock, 'rg', 'app', 'httpget', slot='staging')

        self.assertEqual(result, {'default': 'abc'})
        client_mock.web_apps.list_function_keys_slot.assert_called_once_with('rg', 'app', 'httpget', 'staging')
        client_mock.web_apps.list_function_keys.assert_not_called()


class TestFlexMigrationInPlaceMocked(unittest.TestCase):
    """Unit tests for the --in-place flag on flex-migration start."""

    def test_in_place_payload_matches_create(self):
        flex_sku = {
            'functionAppConfigProperties': {'runtime': {'name': 'python', 'version': '3.11'}},
            'instanceMemoryMB': [{'isDefault': True, 'size': 2048}],
            'maximumInstanceCount': {'defaultValue': 100}
        }
        auth_config = {
            'type': 'StorageAccountConnectionString',
            'storageAccountConnectionStringName': 'DEPLOYMENT_STORAGE_CONNECTION_STRING'
        }

        config = _build_flex_function_app_config(
            'https://storage.blob.core.windows.net/deployment', auth_config, flex_sku,
            None, None, ['function=2'])

        self.assertEqual(config, {
            'deployment': {
                'storage': {
                    'type': 'blobContainer',
                    'value': 'https://storage.blob.core.windows.net/deployment',
                    'authentication': auth_config
                }
            },
            'runtime': {'name': 'python', 'version': '3.11'},
            'scaleAndConcurrency': {
                'maximumInstanceCount': 100,
                'instanceMemoryMB': 2048,
                'alwaysReady': [{'name': 'function', 'instanceCount': 2}]
            }
        })

    def test_in_place_put_uses_same_site_and_preserves_plan(self):
        original_plan_id = '/subscriptions/sub/resourceGroups/src-rg/providers/Microsoft.Web/serverfarms/cv1-plan'
        source = mock.MagicMock()
        source.location = 'eastus'
        source.server_farm_id = original_plan_id
        source.identity = None
        flex_client = mock.MagicMock()
        flex_client.web_apps.list_application_settings.return_value.properties = {
            'AzureWebJobsStorage': 'source-connection-string'
        }
        matched_runtime = mock.MagicMock()
        matched_runtime.sku = {
            'functionAppConfigProperties': {'runtime': {'name': 'python', 'version': '3.11'}},
            'instanceMemoryMB': [{'isDefault': True, 'size': 2048}],
            'maximumInstanceCount': {'defaultValue': 100}
        }

        patches = {
            '_prepare_flex_deployment_storage': mock.DEFAULT,
            '_FlexFunctionAppStackRuntimeHelper': mock.DEFAULT,
            '_prepare_flex_deployment_storage_identity': mock.DEFAULT,
            'web_client_factory': mock.DEFAULT,
            'LongRunningOperation': mock.DEFAULT,
            'get_functionapp': mock.DEFAULT
        }
        with mock.patch.multiple('azure.cli.command_modules.appservice.custom', **patches) as mocks:
            mocks['_prepare_flex_deployment_storage'].return_value = {
                'app_settings_to_add': [],
                'function_app_config': {
                    'deployment': {
                        'storage': {
                            'type': 'blobContainer',
                            'value': 'https://storage.blob.core.windows.net/deployment',
                            'authentication': {
                                'type': 'StorageAccountConnectionString',
                                'storageAccountConnectionStringName': 'AzureWebJobsStorage'
                            }
                        }
                    }
                }
            }
            mocks['_FlexFunctionAppStackRuntimeHelper'].return_value.resolve.return_value = matched_runtime
            mocks['web_client_factory'].return_value = flex_client

            _upgrade_consumption_to_flex_in_place(
                _get_test_cmd(), source, 'src-rg', 'src-app', 'storage', None, None,
                None, None, 'python', '3.11', None, None, None)

        flex_client.web_apps.begin_create_or_update.assert_called_once()
        resource_group, name, payload = flex_client.web_apps.begin_create_or_update.call_args.args
        self.assertEqual((resource_group, name), ('src-rg', 'src-app'))
        self.assertEqual(payload, {
            'location': 'eastus',
            'sku': {'name': 'FlexConsumption'},
            'properties': {
                'serverFarmId': original_plan_id,
                'functionAppConfig': {
                    'deployment': {
                        'storage': {
                            'type': 'blobContainer',
                            'value': 'https://storage.blob.core.windows.net/deployment',
                            'authentication': {
                                'type': 'StorageAccountConnectionString',
                                'storageAccountConnectionStringName': 'AzureWebJobsStorage'
                            }
                        }
                    }
                }
            }
        })
        flex_client.web_apps.update_application_settings.assert_not_called()
        flex_client.app_service_plans.begin_create_or_update.assert_not_called()

    @mock.patch('azure.cli.command_modules.appservice.custom._validate_and_get_deployment_storage')
    def test_in_place_rejects_unsupported_deployment_storage(self, validate_storage_mock):
        flex_sku = {
            'functionAppConfigProperties': {'runtime': {'name': 'python', 'version': '3.11'}},
            'instanceMemoryMB': [{'isDefault': True, 'size': 2048}],
            'maximumInstanceCount': {'defaultValue': 100}
        }
        for sku, hns_enabled, expected_error in [
                ('Premium_LRS', False, 'Premium deployment storage'),
                ('Standard_LRS', True, 'ADLS Gen2 deployment storage')]:
            with self.subTest(sku=sku, hns_enabled=hns_enabled):
                deployment_storage = mock.MagicMock()
                deployment_storage.sku.name = sku
                deployment_storage.is_hns_enabled = hns_enabled
                validate_storage_mock.return_value = deployment_storage

                with self.assertRaises(ValidationError) as ctx:
                    _prepare_flex_deployment_storage(
                        _get_test_cmd(), 'src-rg', 'src-app', 'storage-name', None,
                        'StorageAccountConnectionString', None, 'eastus', flex_sku,
                        None, None, None, validate_for_in_place=True)

                self.assertIn(expected_error, str(ctx.exception))

    def test_in_place_requires_user_assigned_identity_value(self):
        cmd_mock = _get_test_cmd()
        source = mock.MagicMock()
        source.location = 'eastus'

        with self.assertRaises(ArgumentUsageError) as ctx:
            _upgrade_consumption_to_flex_in_place(
                cmd_mock, source, 'src-rg', 'src-app', 'storage-name', None, None,
                'UserAssignedIdentity', None, 'python', '3.11', None, None, None)

        self.assertIn('--deployment-storage-auth-value is required', str(ctx.exception))

    @mock.patch('azure.cli.command_modules.appservice.custom._get_storage_connection_string')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_or_create_deployment_storage_container')
    @mock.patch('azure.cli.command_modules.appservice.custom._validate_and_get_deployment_storage')
    def test_flex_storage_setup_preserves_existing_connection_string_setting(
            self, validate_storage_mock, get_container_mock, get_connection_string_mock):
        deployment_storage = mock.MagicMock()
        deployment_storage.primary_endpoints.blob = 'https://storage.blob.core.windows.net/'
        validate_storage_mock.return_value = deployment_storage
        container = mock.MagicMock()
        container.name = 'deployment'
        get_container_mock.return_value = container
        flex_sku = {
            'functionAppConfigProperties': {'runtime': {'name': 'python', 'version': '3.11'}},
            'instanceMemoryMB': [{'isDefault': True, 'size': 2048}],
            'maximumInstanceCount': {'defaultValue': 100}
        }

        setup = _prepare_flex_deployment_storage(
            _get_test_cmd(), 'src-rg', 'src-app', 'storage-name', 'deployment',
            'StorageAccountConnectionString', 'CUSTOM_DEPLOYMENT_STORAGE', 'eastus', flex_sku,
            None, None, None, {'CUSTOM_DEPLOYMENT_STORAGE': 'existing-value'})

        self.assertEqual(setup['app_settings_to_add'], [])
        self.assertEqual(
            setup['function_app_config']['deployment']['storage']['authentication']
            ['storageAccountConnectionStringName'],
            'CUSTOM_DEPLOYMENT_STORAGE')
        get_connection_string_mock.assert_not_called()

    def test_in_place_polling_failure_retains_side_effects(self):
        source = mock.MagicMock()
        source.location = 'eastus'
        source.server_farm_id = 'cv1-plan-id'
        source.identity = None
        flex_client = mock.MagicMock()
        flex_client.web_apps.list_application_settings.return_value.properties = {
            'AzureWebJobsStorage': 'original-value'
        }
        matched_runtime = mock.MagicMock()
        matched_runtime.sku = {
            'functionAppConfigProperties': {'runtime': {'name': 'python', 'version': '3.11'}},
            'instanceMemoryMB': [{'isDefault': True, 'size': 2048}],
            'maximumInstanceCount': {'defaultValue': 100}
        }
        storage_setup = {
            'app_settings_to_add': [{'name': 'DEPLOYMENT_STORAGE_CONNECTION_STRING', 'value': 'new-value'}],
            'function_app_config': {'deployment': {'storage': {'authentication': {
                'type': 'StorageAccountConnectionString'}}}}
        }
        identity_changes = {'identity_added': True}

        patches = {
            '_prepare_flex_deployment_storage': mock.DEFAULT,
            '_prepare_flex_deployment_storage_identity': mock.DEFAULT,
            '_rollback_flex_deployment_storage_identity': mock.DEFAULT,
            '_cleanup_flex_deployment_storage': mock.DEFAULT,
            '_FlexFunctionAppStackRuntimeHelper': mock.DEFAULT,
            'web_client_factory': mock.DEFAULT,
            'LongRunningOperation': mock.DEFAULT
        }
        with mock.patch.multiple('azure.cli.command_modules.appservice.custom', **patches) as mocks:
            mocks['_prepare_flex_deployment_storage'].return_value = storage_setup
            mocks['_prepare_flex_deployment_storage_identity'].return_value = identity_changes
            mocks['_FlexFunctionAppStackRuntimeHelper'].return_value.resolve.return_value = matched_runtime
            mocks['web_client_factory'].return_value = flex_client
            mocks['LongRunningOperation'].return_value.side_effect = RuntimeError('upgrade failed')

            with self.assertRaisesRegex(RuntimeError, 'upgrade failed'):
                _upgrade_consumption_to_flex_in_place(
                    _get_test_cmd(), source, 'src-rg', 'src-app', 'storage', 'separate-storage', None,
                    None, None, 'python', '3.11', None, None, None)

        self.assertEqual(flex_client.web_apps.update_application_settings.call_count, 1)
        mocks['_rollback_flex_deployment_storage_identity'].assert_not_called()
        mocks['_cleanup_flex_deployment_storage'].assert_not_called()

    def test_in_place_put_rejection_rolls_back_only_unchanged_setting(self):
        source = mock.MagicMock()
        source.location = 'eastus'
        source.server_farm_id = 'cv1-plan-id'
        source.identity = None
        flex_client = mock.MagicMock()
        flex_client.web_apps.list_application_settings.side_effect = [
            mock.MagicMock(properties={'AzureWebJobsStorage': 'original-value'}),
            mock.MagicMock(properties={
                'AzureWebJobsStorage': 'original-value',
                'DEPLOYMENT_STORAGE_CONNECTION_STRING': 'new-value',
                'CONCURRENT_SETTING': 'preserve-me'
            })
        ]
        flex_client.web_apps.begin_create_or_update.side_effect = RuntimeError('request rejected')
        matched_runtime = mock.MagicMock()
        matched_runtime.sku = {
            'functionAppConfigProperties': {'runtime': {'name': 'python', 'version': '3.11'}},
            'instanceMemoryMB': [{'isDefault': True, 'size': 2048}],
            'maximumInstanceCount': {'defaultValue': 100}
        }
        storage_setup = {
            'app_settings_to_add': [{'name': 'DEPLOYMENT_STORAGE_CONNECTION_STRING', 'value': 'new-value'}],
            'function_app_config': {'deployment': {'storage': {'authentication': {
                'type': 'StorageAccountConnectionString'}}}}
        }
        identity_changes = {'identity_added': True}

        patches = {
            '_prepare_flex_deployment_storage': mock.DEFAULT,
            '_prepare_flex_deployment_storage_identity': mock.DEFAULT,
            '_rollback_flex_deployment_storage_identity': mock.DEFAULT,
            '_cleanup_flex_deployment_storage': mock.DEFAULT,
            '_FlexFunctionAppStackRuntimeHelper': mock.DEFAULT,
            'web_client_factory': mock.DEFAULT
        }
        with mock.patch.multiple('azure.cli.command_modules.appservice.custom', **patches) as mocks:
            mocks['_prepare_flex_deployment_storage'].return_value = storage_setup
            mocks['_prepare_flex_deployment_storage_identity'].return_value = identity_changes
            mocks['_FlexFunctionAppStackRuntimeHelper'].return_value.resolve.return_value = matched_runtime
            mocks['web_client_factory'].return_value = flex_client

            with self.assertRaisesRegex(RuntimeError, 'request rejected'):
                _upgrade_consumption_to_flex_in_place(
                    _get_test_cmd(), source, 'src-rg', 'src-app', 'storage', 'separate-storage', None,
                    None, None, 'python', '3.11', None, None, None)

        self.assertEqual(flex_client.web_apps.update_application_settings.call_count, 2)
        restored_settings = flex_client.web_apps.update_application_settings.call_args.args[2]
        self.assertEqual(restored_settings.properties, {
            'AzureWebJobsStorage': 'original-value',
            'CONCURRENT_SETTING': 'preserve-me'
        })
        mocks['_rollback_flex_deployment_storage_identity'].assert_called_once_with(
            mock.ANY, 'src-rg', 'src-app', identity_changes)
        mocks['_cleanup_flex_deployment_storage'].assert_called_once_with(
            mock.ANY, 'src-rg', storage_setup)

    @mock.patch('azure.cli.command_modules.appservice.custom._assign_deployment_storage_managed_identity_role')
    @mock.patch('azure.cli.command_modules.appservice.custom.'
                '_has_deployment_storage_role_assignment_on_resource', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom.assign_identity')
    def test_in_place_prepares_user_assigned_identity(
            self, assign_identity_mock, has_role_assignment_mock, assign_role_mock):
        cmd_mock = _get_test_cmd()
        deployment_storage = mock.MagicMock()
        deployment_identity = mock.MagicMock()
        deployment_identity.principal_id = 'identity-principal-id'

        assignment = mock.MagicMock()
        assignment.id = 'role-assignment-id'
        assign_role_mock.return_value = assignment
        storage_setup = {
            'deployment_storage': deployment_storage,
            'deployment_storage_name': 'storage-name',
            'deployment_storage_auth_value': 'identity-resource-id',
            'user_assigned_identity': deployment_identity,
            'function_app_config': {
                'deployment': {'storage': {'authentication': {'type': 'UserAssignedIdentity'}}}
            }
        }

        changes = _prepare_flex_deployment_storage_identity(
            cmd_mock, 'src-rg', 'src-app', storage_setup)

        assign_identity_mock.assert_called_once_with(
            cmd_mock, 'src-rg', 'src-app', ['identity-resource-id'])
        has_role_assignment_mock.assert_called_once_with(
            cmd_mock.cli_ctx, deployment_storage, 'identity-principal-id')
        assign_role_mock.assert_called_once_with(
            cmd_mock.cli_ctx, deployment_storage, 'identity-principal-id')
        self.assertTrue(changes['identity_added'])
        self.assertEqual(changes['role_assignment_id'], 'role-assignment-id')

    @mock.patch('azure.cli.command_modules.appservice.custom._assign_deployment_storage_managed_identity_role')
    @mock.patch('azure.cli.command_modules.appservice.custom.'
                '_has_deployment_storage_role_assignment_on_resource', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom.assign_identity')
    def test_in_place_prepares_system_assigned_identity(
            self, assign_identity_mock, has_role_assignment_mock, assign_role_mock):
        cmd_mock = _get_test_cmd()
        deployment_storage = mock.MagicMock()
        deployment_storage.id = 'storage-resource-id'
        assigned_identity = mock.MagicMock()
        assigned_identity.principal_id = 'system-principal-id'
        assign_identity_mock.return_value = assigned_identity
        assignment = mock.MagicMock()
        assignment.id = 'role-assignment-id'
        assign_role_mock.return_value = assignment
        storage_setup = {
            'deployment_storage': deployment_storage,
            'deployment_storage_name': 'storage-name',
            'deployment_storage_auth_value': None,
            'function_app_config': {
                'deployment': {'storage': {'authentication': {'type': 'SystemAssignedIdentity'}}}
            }
        }

        changes = _prepare_flex_deployment_storage_identity(
            cmd_mock, 'src-rg', 'src-app', storage_setup)

        assign_identity_mock.assert_called_once_with(
            cmd_mock, 'src-rg', 'src-app', ['[system]'])
        has_role_assignment_mock.assert_called_once_with(
            cmd_mock.cli_ctx, deployment_storage, 'system-principal-id')
        assign_role_mock.assert_called_once_with(
            cmd_mock.cli_ctx, deployment_storage, 'system-principal-id')
        self.assertTrue(changes['identity_added'])

    def test_in_place_rejects_target_name_arg(self):
        """--in-place with --name should raise MutuallyExclusiveArgumentError."""
        cmd_mock = _get_test_cmd()
        with self.assertRaises(MutuallyExclusiveArgumentError):
            migrate_consumption_to_flex(cmd_mock,
                                        source_resource_group='src-rg',
                                        source_name='src-app',
                                        resource_group=None,
                                        name='target-app',
                                        in_place=True)

    def test_in_place_rejects_target_resource_group_arg(self):
        """--in-place with --resource-group should raise MutuallyExclusiveArgumentError."""
        cmd_mock = _get_test_cmd()
        with self.assertRaises(MutuallyExclusiveArgumentError):
            migrate_consumption_to_flex(cmd_mock,
                                        source_resource_group='src-rg',
                                        source_name='src-app',
                                        resource_group='target-rg',
                                        name=None,
                                        in_place=True)

    def test_in_place_rejects_both_target_args(self):
        """--in-place with both --name and --resource-group should raise MutuallyExclusiveArgumentError."""
        cmd_mock = _get_test_cmd()
        with self.assertRaises(MutuallyExclusiveArgumentError):
            migrate_consumption_to_flex(cmd_mock,
                                        source_resource_group='src-rg',
                                        source_name='src-app',
                                        resource_group='target-rg',
                                        name='target-app',
                                        in_place=True)

    def test_side_by_side_requires_name(self):
        """Side-by-side (no --in-place) without --name should raise RequiredArgumentMissingError."""
        cmd_mock = _get_test_cmd()
        with self.assertRaises(RequiredArgumentMissingError):
            migrate_consumption_to_flex(cmd_mock,
                                        source_resource_group='src-rg',
                                        source_name='src-app',
                                        resource_group='target-rg',
                                        name=None,
                                        in_place=False)

    def test_side_by_side_requires_resource_group(self):
        """Side-by-side (no --in-place) without --resource-group should raise RequiredArgumentMissingError."""
        cmd_mock = _get_test_cmd()
        with self.assertRaises(RequiredArgumentMissingError):
            migrate_consumption_to_flex(cmd_mock,
                                        source_resource_group='src-rg',
                                        source_name='src-app',
                                        resource_group=None,
                                        name='target-app',
                                        in_place=False)

    def test_side_by_side_unchanged(self):
        source = mock.MagicMock()
        source.location = 'eastus'
        source.name = 'src-app'
        site_configs = mock.MagicMock()
        result = mock.sentinel.result
        patches = {
            'get_mgmt_service_client': mock.DEFAULT,
            'list_flexconsumption_locations': mock.DEFAULT,
            '_is_linux_consumption_function_app': mock.DEFAULT,
            'validate_flex_migration_eligibility_for_linux_consumption_app': mock.DEFAULT,
            'list_slots': mock.DEFAULT,
            'get_site_configs': mock.DEFAULT,
            '_get_functionapp_runtime_info_helper': mock.DEFAULT,
            'create_functionapp': mock.DEFAULT,
            '_migrate_app_settings': mock.DEFAULT,
            '_migrate_site_configs': mock.DEFAULT,
            '_migrate_site_properties': mock.DEFAULT,
            '_migrate_basic_publishing_credentials_policies': mock.DEFAULT,
            'get_functionapp': mock.DEFAULT
        }
        with mock.patch.multiple('azure.cli.command_modules.appservice.custom', **patches) as mocks:
            mocks['get_mgmt_service_client'].return_value.web_apps.get.return_value = source
            mocks['list_flexconsumption_locations'].return_value = [{'name': 'eastus'}]
            mocks['_is_linux_consumption_function_app'].return_value = True
            mocks['validate_flex_migration_eligibility_for_linux_consumption_app'].return_value = (True, [])
            mocks['list_slots'].return_value = []
            mocks['get_site_configs'].return_value = site_configs
            mocks['_get_functionapp_runtime_info_helper'].return_value = {
                'app_runtime': 'python',
                'app_runtime_version': '3.11'
            }
            mocks['get_functionapp'].return_value = result

            actual = migrate_consumption_to_flex(
                _get_test_cmd(), 'src-rg', 'src-app', resource_group='target-rg', name='target-app',
                storage_account='storage', skip_managed_identities=True, skip_access_restrictions=True,
                skip_storage_mount=True, skip_hostnames=True, skip_cors=True)

        self.assertIs(actual, result)
        mocks['create_functionapp'].assert_called_once_with(
            mock.ANY, 'target-rg', 'target-app', 'storage', flexconsumption_location='eastus',
            runtime='python', runtime_version='3.11', maximum_instance_count=None)
        mocks['_migrate_app_settings'].assert_called_once_with(
            mock.ANY, 'src-rg', 'src-app', 'target-rg', 'target-app', 'storage')

    @mock.patch('azure.cli.command_modules.appservice.custom.get_mgmt_service_client')
    @mock.patch('azure.cli.command_modules.appservice.custom.list_flexconsumption_locations', return_value=[{'name': 'eastus'}])
    @mock.patch('azure.cli.command_modules.appservice.custom.is_flex_functionapp', return_value=True)
    def test_in_place_rejects_already_flex(self, is_flex_mock, list_locations_mock, get_client_mock):
        """--in-place on an already-Flex app should raise ValidationError."""
        cmd_mock = _get_test_cmd()
        # Mock the web client to return a site
        client_mock = mock.MagicMock()
        site_mock = mock.MagicMock()
        site_mock.kind = 'functionapp,linux'
        site_mock.name = 'src-app'
        client_mock.web_apps.get.return_value = site_mock
        get_client_mock.return_value = client_mock

        with self.assertRaises(ValidationError) as ctx:
            migrate_consumption_to_flex(cmd_mock,
                                        source_resource_group='src-rg',
                                        source_name='src-app',
                                        in_place=True)
        self.assertIn('already on Flex Consumption', str(ctx.exception))

    @mock.patch('azure.cli.command_modules.appservice.custom.get_mgmt_service_client')
    @mock.patch('azure.cli.command_modules.appservice.custom.list_flexconsumption_locations', return_value=[{'name': 'eastus'}])
    @mock.patch('azure.cli.command_modules.appservice.custom.is_flex_functionapp', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom._is_linux_consumption_function_app', return_value=False)
    def test_in_place_rejects_non_consumption(self, is_linux_consumption_mock, is_flex_mock,
                                               list_locations_mock, get_client_mock):
        """--in-place on a non-Consumption app should raise ValidationError."""
        cmd_mock = _get_test_cmd()
        client_mock = mock.MagicMock()
        site_mock = mock.MagicMock()
        site_mock.kind = 'functionapp'
        site_mock.name = 'src-app'
        client_mock.web_apps.get.return_value = site_mock
        get_client_mock.return_value = client_mock

        with self.assertRaises(ValidationError) as ctx:
            migrate_consumption_to_flex(cmd_mock,
                                        source_resource_group='src-rg',
                                        source_name='src-app',
                                        in_place=True)
        self.assertIn('not on a Linux Dynamic (Consumption) plan', str(ctx.exception))


class TestFlexMigrationRevertMocked(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.appservice.custom.get_raw_functionapp',
                return_value={'properties': {'sku': 'Dynamic'}})
    def test_revert_rejects_non_flex_app(self, get_raw_functionapp_mock):
        cmd_mock = _get_test_cmd()

        with self.assertRaises(ValidationError) as ctx:
            revert_flex_migration(cmd_mock, 'src-rg', 'src-app')

        self.assertIn('not on Flex Consumption', str(ctx.exception))
        get_raw_functionapp_mock.assert_called_once_with(cmd_mock.cli_ctx, 'src-rg', 'src-app')

    @mock.patch('azure.cli.command_modules.appservice.custom.get_functionapp')
    @mock.patch('azure.cli.command_modules.appservice.custom.LongRunningOperation')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory')
    @mock.patch('azure.cli.command_modules.appservice.custom.get_raw_functionapp',
                return_value={'location': 'North Central US (Stage)',
                              'properties': {'sku': 'FlexConsumption'}})
    def test_revert_submits_dynamic_sku(self, get_raw_functionapp_mock, web_client_factory_mock,
                                        long_running_operation_mock, get_functionapp_mock):
        cmd_mock = _get_test_cmd()
        result_mock = mock.sentinel.result
        get_functionapp_mock.return_value = result_mock

        client_mock = mock.MagicMock()
        poller_mock = client_mock.web_apps.begin_create_or_update.return_value
        web_client_factory_mock.return_value = client_mock

        result = revert_flex_migration(cmd_mock, 'src-rg', 'src-app')

        self.assertIs(result, result_mock)
        request = client_mock.web_apps.begin_create_or_update.call_args.args[2]
        self.assertEqual(request, {
            'kind': 'functionapp,linux',
            'location': 'North Central US (Stage)',
            'properties': {
                'reserved': True,
                'sku': 'Dynamic'
            },
            'sku': {'name': 'Dynamic'}
        })
        client_mock.web_apps.get.assert_not_called()
        long_running_operation_mock.assert_called_once_with(cmd_mock.cli_ctx)
        long_running_operation_mock.return_value.assert_called_once_with(poller_mock)
        get_functionapp_mock.assert_called_once_with(cmd_mock, 'src-rg', 'src-app')


_REGISTRY_SUBSCRIPTION = '00000000-0000-0000-0000-000000000000'
_REGISTRY_SITE = 'subscriptions/{}/resourceGroups/rg/providers/Microsoft.Web/sites/app'.format(_REGISTRY_SUBSCRIPTION)
_REGISTRY_IDENTITY = ('/subscriptions/{}/resourceGroups/rg/providers/Microsoft.ManagedIdentity/'
                      'userAssignedIdentities/acr-pull'.format(_REGISTRY_SUBSCRIPTION))
_REGISTRY_DIGEST = 'sha256:' + 'a' * 64
_REGISTRY_SECRET = 'SENTINEL-REGISTRY-PASSWORD-2f9c'


def _flex_blob_site():
    return {
        'id': '/' + _REGISTRY_SITE,
        'name': 'app',
        'kind': 'functionapp,linux',
        'location': 'East US',
        'tags': {'team': 'functions'},
        'properties': {
            'sku': 'FlexConsumption',
            'serverFarmId': '/subscriptions/{}/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan'.format(
                _REGISTRY_SUBSCRIPTION),
            'unknownSiteProperty': {'keep': True},
            'functionAppConfig': {
                'deployment': {
                    'storage': {
                        'type': 'blobContainer',
                        'value': 'https://sa.blob.core.windows.net/app-package-app',
                        'authentication': {
                            'type': 'StorageAccountConnectionString',
                            'userAssignedIdentityResourceId': None,
                            'storageAccountConnectionStringName': 'DEPLOYMENT_STORAGE_CONNECTION_STRING'
                        }
                    }
                },
                'runtime': {'name': 'python', 'version': '3.11'},
                'scaleAndConcurrency': {
                    'alwaysReady': [{'name': 'http', 'instanceCount': 1}],
                    'maximumInstanceCount': 40,
                    'instanceMemoryMB': 4096,
                    'triggers': {'http': {'perInstanceConcurrency': 8}}
                },
                'siteUpdateStrategy': {'type': 'RollingUpdate'},
                'unknownFunctionAppConfigProperty': {'keep': True}
            }
        }
    }


def _flex_registry_site():
    # Shape returned by the service: runtime is null and the fields of other authentication modes are null.
    site = _flex_blob_site()
    function_app_config = site['properties']['functionAppConfig']
    function_app_config['runtime'] = None
    function_app_config['deployment']['storage'] = {
        'type': 'Registry',
        'value': 'myacr.azurecr.io/app:v1',
        'authentication': {
            'type': 'UserAssignedIdentity',
            'userAssignedIdentityResourceId': _REGISTRY_IDENTITY,
            'storageAccountConnectionStringName': None,
            'usernameSettingName': None,
            'passwordSettingName': None,
            'serverUrl': None
        }
    }
    return site


def _with_registry_storage(site, storage):
    function_app_config = site['properties']['functionAppConfig']
    del function_app_config['runtime']
    function_app_config['deployment']['storage'] = storage
    return site


class _FakeArmSite:
    """Stands in for ARM behind requests.Session.send, so the real send_raw_request builds, sends and logs requests.

    Stores one site, echoes accepted PUT bodies, serves a sentinel secret from the app settings endpoint, and leaves
    the Registry authentication fields out of GET responses for API versions older than 2025-05-01.
    """

    def __init__(self, site, put_error=None):
        self.site = site
        self.put_error = put_error
        self.requests = []

    def send(self, _session, request, **_kwargs):
        import requests
        body = json.loads(request.body) if request.body else None
        self.requests.append((request.method, request.url, body))
        status, payload = 200, self.site
        if '/config/appsettings/list' in request.url:
            payload = {'properties': {'REGISTRY_PASSWORD': _REGISTRY_SECRET}}
        elif request.method == 'GET' and 'api-version=2025-05-01' not in request.url:
            # Only 2025-05-01 publishes the Registry authentication fields, so older versions may omit them.
            payload = json.loads(json.dumps(self.site))
            authentication = payload['properties']['functionAppConfig']['deployment']['storage']['authentication']
            for field in ('usernameSettingName', 'passwordSettingName', 'serverUrl'):
                authentication.pop(field, None)
        elif request.method == 'PUT':
            if self.put_error:
                status, payload = 400, self.put_error
            else:
                self.site = payload = body
        response = requests.Response()
        response.status_code = status
        response.reason = 'OK' if status == 200 else 'Bad Request'
        response.headers['Content-Type'] = 'application/json'
        response._content = json.dumps(payload).encode()  # pylint: disable=protected-access
        response.raw = mock.Mock()
        response.raw.stream.return_value = iter([response._content])  # pylint: disable=protected-access
        response.url = request.url
        return response

    def calls(self):
        return [(method, urlparse(url).path.lstrip('/'), parse_qs(urlparse(url).query)['api-version'][0])
                for method, url, _ in self.requests]


@contextmanager
def _fake_arm(site, put_error=None):
    arm = _FakeArmSite(site, put_error)
    with mock.patch('requests.Session.send', autospec=True, side_effect=arm.send), \
            mock.patch('azure.cli.core._profile.Profile.get_raw_token',
                       return_value=(('Bearer', 'token', None), _REGISTRY_SUBSCRIPTION, 'tenant')), \
            mock.patch('azure.cli.command_modules.appservice.utils.get_subscription_id',
                       return_value=_REGISTRY_SUBSCRIPTION), \
            mock.patch('azure.cli.core.commands.client_factory.get_subscription_id',
                       return_value=_REGISTRY_SUBSCRIPTION):
        yield arm


class TestFlexRegistryDeploymentConfigMocked(unittest.TestCase):
    """`functionapp deployment config set/show` and `functionapp show` with Registry storage, asserted on the HTTP
    requests sent to ARM."""

    def setUp(self):
        self.cmd = _get_test_cmd()

    def test_set_switches_blob_app_to_registry_with_exact_payload(self):
        basic_args = {'deployment_image_auth_type': 'Basic', 'deployment_image_username_setting': 'REGISTRY_USERNAME',
                      'deployment_image_password_setting': 'REGISTRY_PASSWORD'}
        basic_auth = {'type': 'Basic', 'usernameSettingName': 'REGISTRY_USERNAME',
                      'passwordSettingName': 'REGISTRY_PASSWORD'}
        cases = [
            ('Anonymous, tag only', 'mcr.microsoft.com/azure-functions/dotnet-isolated:4-dotnet-isolated8.0',
             {'deployment_image_auth_type': 'Anonymous'}, {'type': 'Anonymous'}),
            ('SystemAssignedIdentity, digest only', 'myacr.azurecr.io/app@' + _REGISTRY_DIGEST,
             {'deployment_image_auth_type': 'SystemAssignedIdentity'}, {'type': 'SystemAssignedIdentity'}),
            ('UserAssignedIdentity, tag and digest', 'myacr.azurecr.io/app:v1@' + _REGISTRY_DIGEST,
             {'deployment_image_auth_type': 'UserAssignedIdentity', 'deployment_image_identity': _REGISTRY_IDENTITY},
             {'type': 'UserAssignedIdentity', 'userAssignedIdentityResourceId': _REGISTRY_IDENTITY}),
            ('Basic', 'registry.contoso.com:5000/team/app:v1', basic_args, basic_auth),
            ('Basic with server URL', 'registry.contoso.com:5000/team/app:v1',
             dict(basic_args, deployment_image_server_url='https://registry.contoso.com:5000'),
             dict(basic_auth, serverUrl='https://registry.contoso.com:5000')),
        ]
        for case, image, auth_args, authentication in cases:
            with self.subTest(case):
                storage = {'type': 'Registry', 'value': image, 'authentication': authentication}
                with _fake_arm(_flex_blob_site()) as arm:
                    result = update_deployment_configs(self.cmd, 'rg', 'app', deployment_image=image, **auth_args)
                    shown = get_deployment_configs(self.cmd, 'rg', 'app')

                self.assertEqual(arm.calls(), [('GET', _REGISTRY_SITE, '2025-05-01'),
                                               ('PUT', _REGISTRY_SITE, '2025-05-01'),
                                               ('GET', _REGISTRY_SITE, '2023-12-01'),
                                               ('GET', _REGISTRY_SITE, '2025-05-01')])
                self.assertEqual(arm.requests[1][2], _with_registry_storage(_flex_blob_site(), storage))
                self.assertEqual(result, {'storage': storage})
                self.assertEqual(shown, {'storage': storage})

    def test_show_reads_registry_apps_with_the_registry_api_version_and_blob_apps_unchanged(self):
        registry_deployment = _flex_registry_site()['properties']['functionAppConfig']['deployment']
        blob_deployment = _flex_blob_site()['properties']['functionAppConfig']['deployment']
        cases = [
            ('functionapp show, Registry', show_functionapp, _flex_registry_site,
             ['2023-12-01', '2023-12-01', '2025-05-01'], _flex_registry_site()),
            ('functionapp show, blob', show_functionapp, _flex_blob_site,
             ['2023-12-01', '2023-12-01'], _flex_blob_site()),
            ('deployment config show, Registry', get_deployment_configs, _flex_registry_site,
             ['2023-12-01', '2025-05-01'], registry_deployment),
            ('deployment config show, blob', get_deployment_configs, _flex_blob_site,
             ['2023-12-01'], blob_deployment),
        ]
        for case, show, site, api_versions, expected in cases:
            with self.subTest(case):
                with _fake_arm(site()) as arm:
                    result = show(self.cmd, 'rg', 'app')

                self.assertEqual(arm.calls(), [('GET', _REGISTRY_SITE, version) for version in api_versions])
                self.assertEqual(result, expected)

    def test_set_on_registry_app_keeps_the_unspecified_image_or_authentication(self):
        cases = [
            ('image only', {'deployment_image': 'myacr.azurecr.io/app:v2'},
             {'type': 'Registry', 'value': 'myacr.azurecr.io/app:v2',
              'authentication': {'type': 'UserAssignedIdentity',
                                 'userAssignedIdentityResourceId': _REGISTRY_IDENTITY}}),
            ('authentication only', {'deployment_image_auth_type': 'SystemAssignedIdentity'},
             {'type': 'Registry', 'value': 'myacr.azurecr.io/app:v1',
              'authentication': {'type': 'SystemAssignedIdentity'}}),
        ]
        for case, args, storage in cases:
            with self.subTest(case):
                with _fake_arm(_flex_registry_site()) as arm:
                    update_deployment_configs(self.cmd, 'rg', 'app', **args)

                self.assertEqual([method for method, _, _ in arm.requests], ['GET', 'PUT'])
                self.assertEqual(arm.requests[1][2], _with_registry_storage(_flex_registry_site(), storage))

    def test_set_rejects_invalid_registry_arguments_without_writing(self):
        image_args = {'deployment_image': 'myacr.azurecr.io/app:v1', 'deployment_image_auth_type': 'Anonymous'}
        basic_args = {'deployment_image_auth_type': 'Basic', 'deployment_image_username_setting': 'REGISTRY_USERNAME',
                      'deployment_image_password_setting': 'REGISTRY_PASSWORD'}
        cases = [
            ('authentication argument without type', _flex_registry_site,
             {'deployment_image_identity': _REGISTRY_IDENTITY}, RequiredArgumentMissingError),
            ('empty user-assigned identity', _flex_registry_site,
             {'deployment_image_auth_type': 'UserAssignedIdentity', 'deployment_image_identity': ''},
             RequiredArgumentMissingError),
            ('Basic without password setting', _flex_registry_site,
             {'deployment_image_auth_type': 'Basic', 'deployment_image_username_setting': 'REGISTRY_USERNAME'},
             RequiredArgumentMissingError),
            ('identity with Basic', _flex_registry_site,
             dict(basic_args, deployment_image_identity=_REGISTRY_IDENTITY), ArgumentUsageError),
            ('server URL without Basic', _flex_registry_site,
             dict(image_args, deployment_image_server_url='https://myacr.azurecr.io'), ArgumentUsageError),
            ('Registry and blob arguments together', _flex_blob_site,
             dict(image_args, deployment_storage_auth_type='SystemAssignedIdentity'), MutuallyExclusiveArgumentError),
            ('switch from blob without authentication', _flex_blob_site,
             {'deployment_image': 'myacr.azurecr.io/app:v1'}, RequiredArgumentMissingError),
            ('switch from blob without image', _flex_blob_site,
             {'deployment_image_auth_type': 'Anonymous'}, RequiredArgumentMissingError),
            ('blob arguments on a Registry app', _flex_registry_site,
             {'deployment_storage_auth_type': 'SystemAssignedIdentity'}, ValidationError),
        ]
        for case, site, args, error in cases:
            with self.subTest(case):
                with _fake_arm(site()) as arm, self.assertRaises(error):
                    update_deployment_configs(self.cmd, 'rg', 'app', **args)
                self.assertNotIn('PUT', [method for method, _, _ in arm.requests])

    def test_set_surfaces_service_rejection_and_show_confirms_the_previous_config(self):
        # The CLI doesn't parse image references; the service rejects invalid ones with a field-scoped error.
        field_error = {'Code': 'BadRequest', 'Message': 'The parameter Site.FunctionAppConfig.Deployment.Storage.Value '
                                                        'has an invalid value.'}
        with _fake_arm(_flex_registry_site(), put_error=field_error) as arm:
            with self.assertRaises(HTTPError) as error:
                update_deployment_configs(self.cmd, 'rg', 'app', deployment_image='myacr.azurecr.io/App:Latest!')
            shown = get_deployment_configs(self.cmd, 'rg', 'app')

        self.assertIn('Site.FunctionAppConfig.Deployment.Storage.Value', str(error.exception))
        self.assertEqual([method for method, _, _ in arm.requests], ['GET', 'PUT', 'GET', 'GET'])
        self.assertEqual(arm.requests[1][2]['properties']['functionAppConfig']['deployment']['storage']['value'],
                         'myacr.azurecr.io/App:Latest!')
        self.assertEqual(shown, _flex_registry_site()['properties']['functionAppConfig']['deployment'])

    def test_set_and_show_log_setting_names_but_never_registry_secrets(self):
        with _fake_arm(_flex_blob_site()), \
                self.assertLogs('cli.azure.cli.core.util', level='DEBUG') as logs:
            outputs = [
                update_deployment_configs(
                    self.cmd, 'rg', 'app', deployment_image='myacr.azurecr.io/app:v1',
                    deployment_image_auth_type='Basic', deployment_image_username_setting='REGISTRY_USERNAME',
                    deployment_image_password_setting='REGISTRY_PASSWORD'),
                get_deployment_configs(self.cmd, 'rg', 'app'),
                show_functionapp(self.cmd, 'rg', 'app')]

        debug_log, output = '\n'.join(logs.output), json.dumps(outputs)
        self.assertIn('"passwordSettingName": "REGISTRY_PASSWORD"', debug_log)
        self.assertEqual(output.count('"passwordSettingName": "REGISTRY_PASSWORD"'), 3)
        self.assertNotIn(_REGISTRY_SECRET, debug_log + output)

    def test_other_flex_config_writes_preserve_basic_registry_storage(self):
        cases = [
            ('scale', update_scale_config, {'maximum_instance_count': 50},
             'scaleAndConcurrency', 'maximumInstanceCount', 50),
            ('always-ready set', update_always_ready_settings, {'settings': ['http=2']},
             'scaleAndConcurrency', 'alwaysReady', [{'name': 'http', 'instanceCount': 2}]),
            ('always-ready delete', delete_always_ready_settings, {'setting_names': ['http']},
             'scaleAndConcurrency', 'alwaysReady', []),
            ('update strategy', set_update_strategy_config, {'strategy_type': 'Recreate'},
             'siteUpdateStrategy', 'type', 'Recreate'),
        ]
        authentication = {'type': 'Basic', 'usernameSettingName': 'REGISTRY_USERNAME',
                          'passwordSettingName': 'REGISTRY_PASSWORD', 'serverUrl': 'https://myacr.azurecr.io'}
        for case, update, args, section, field, expected in cases:
            with self.subTest(case):
                site = _flex_registry_site()
                site['properties']['functionAppConfig']['deployment']['storage']['authentication'].update(
                    authentication, userAssignedIdentityResourceId=None)
                with _fake_arm(site) as arm:
                    update(self.cmd, 'rg', 'app', **args)
                    shown = get_deployment_configs(self.cmd, 'rg', 'app')

                self.assertEqual(arm.calls(), [('GET', _REGISTRY_SITE, '2023-12-01'),
                                               ('GET', _REGISTRY_SITE, '2025-05-01'),
                                               ('PUT', _REGISTRY_SITE, '2025-05-01'),
                                               ('GET', _REGISTRY_SITE, '2023-12-01'),
                                               ('GET', _REGISTRY_SITE, '2025-05-01')])
                sent = arm.requests[2][2]['properties']['functionAppConfig']
                self.assertEqual(sent['deployment']['storage']['authentication'], authentication)
                self.assertEqual(shown['storage']['authentication'], authentication)
                self.assertEqual(shown['storage']['value'], 'myacr.azurecr.io/app:v1')
                self.assertNotIn('runtime', sent)
                self.assertEqual(sent[section][field], expected)
                self.assertEqual(sent['unknownFunctionAppConfigProperty'], {'keep': True})

    def test_other_flex_config_writes_keep_blob_requests_unchanged(self):
        cases = [
            ('scale', update_scale_config, {'maximum_instance_count': 50}),
            ('always-ready set', update_always_ready_settings, {'settings': ['http=2']}),
            ('always-ready delete', delete_always_ready_settings, {'setting_names': ['http']}),
            ('update strategy', set_update_strategy_config, {'strategy_type': 'Recreate'}),
        ]
        for case, update, args in cases:
            with self.subTest(case):
                site = _flex_blob_site()
                with _fake_arm(site) as arm:
                    update(self.cmd, 'rg', 'app', **args)

                self.assertEqual(arm.calls(), [('GET', _REGISTRY_SITE, '2023-12-01'),
                                               ('PUT', _REGISTRY_SITE, '2023-12-01')])
                sent = arm.requests[1][2]['properties']['functionAppConfig']
                self.assertEqual(sent['deployment'], site['properties']['functionAppConfig']['deployment'])
                self.assertEqual(sent['runtime'], {'name': 'python', 'version': '3.11'})

    def test_runtime_set_rejects_registry_storage_without_writing(self):
        with _fake_arm(_flex_registry_site()) as arm, self.assertRaisesRegex(ValidationError, 'Registry.*runtime'):
            update_runtime_config(self.cmd, 'rg', 'app', runtime_version='3.12')

        self.assertEqual(arm.calls(), [('GET', _REGISTRY_SITE, '2023-12-01')])


class TestFlexRegistryIdentityMocked(unittest.TestCase):
    def test_identity_changes_preserve_registry_authentication_and_blob_requests(self):
        from azure.core.credentials import AccessToken

        credential = mock.Mock()
        credential.get_token.return_value = AccessToken('token', 2147483647)

        def client_factory(_cli_ctx, api_version=None):
            return WebSiteManagementClient(credential, _REGISTRY_SUBSCRIPTION,
                                           api_version=api_version or '2023-12-01')

        actions = [
            ('assign', assign_identity, None, 'SystemAssigned'),
            ('remove', remove_identity, {'type': 'SystemAssigned'}, 'None'),
        ]
        storage_cases = [
            ('Registry Basic', _flex_registry_site, ['2023-12-01', '2025-05-01', '2025-05-01']),
            ('Blob', _flex_blob_site, ['2023-12-01', '2023-12-01']),
        ]
        for action, update, starting_identity, expected_identity_type in actions:
            for storage_type, make_site, versions in storage_cases:
                with self.subTest(action=action, storage=storage_type):
                    site = make_site()
                    if starting_identity:
                        site['identity'] = starting_identity
                    if storage_type == 'Registry Basic':
                        site['properties']['functionAppConfig']['deployment']['storage']['authentication'].update(
                            type='Basic', userAssignedIdentityResourceId=None,
                            usernameSettingName='REGISTRY_USERNAME', passwordSettingName='REGISTRY_PASSWORD')
                    cmd = _get_test_cmd()
                    with _fake_arm(site) as arm, \
                            mock.patch('azure.cli.command_modules.appservice._appservice_utils.web_client_factory',
                                       side_effect=client_factory), \
                            mock.patch('azure.cli.command_modules.appservice.custom.LongRunningOperation',
                                       side_effect=lambda _ctx: lambda poller: poller.result()):
                        identity = update(cmd, 'rg', 'app', ['[system]'])

                    self.assertEqual(arm.calls(), [(method, _REGISTRY_SITE, version) for method, version in
                                                   zip(['GET'] * (len(versions) - 1) + ['PUT'], versions)])
                    sent = arm.requests[-1][2]
                    self.assertEqual(sent['identity']['type'], expected_identity_type)
                    self.assertIsNotNone(identity)
                    config = sent['properties']['functionAppConfig']
                    if storage_type == 'Registry Basic':
                        self.assertEqual(config['deployment']['storage']['authentication'], {
                            'type': 'Basic', 'usernameSettingName': 'REGISTRY_USERNAME',
                            'passwordSettingName': 'REGISTRY_PASSWORD'})
                        self.assertNotIn('runtime', config)
                        self.assertEqual(config['unknownFunctionAppConfigProperty'], {'keep': True})
                    else:
                        self.assertEqual(config['deployment'], site['properties']['functionAppConfig']['deployment'])
                        self.assertEqual(config['runtime'], {'name': 'python', 'version': '3.11'})


class TestFlexRegistryCreateMocked(unittest.TestCase):
    """`functionapp create --deployment-image` builds a Registry functionAppConfig without a runtime."""

    def setUp(self):
        self.cmd = _get_test_cmd()
        self.web_client_factory = self._patch('web_client_factory')
        self._patch('list_flexconsumption_locations', return_value=[{'name': 'eastus'}])
        self._patch('is_storage_account_network_restricted', return_value=False)
        self._patch('_validate_and_get_connection_string', return_value='storage-connection-string')
        self._patch('create_flex_app_service_plan', return_value=mock.Mock(id='plan-id'))
        self._patch('LongRunningOperation')
        self._patch('_set_remote_or_local_git')
        self.create_app_insights = self._patch('try_create_workspace_based_application_insights')
        self.assign_identity = self._patch('assign_identity')
        self.get_raw_functionapp = self._patch('get_raw_functionapp')
        self.runtime_helper = self._patch('_FlexFunctionAppStackRuntimeHelper')
        self.prepare_storage = self._patch('_prepare_flex_deployment_storage')
        self.prepare_storage_identity = self._patch('_prepare_flex_deployment_storage_identity')

    def _patch(self, name, **kwargs):
        patcher = mock.patch('azure.cli.command_modules.appservice.custom.' + name, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _created_site(self):
        self.web_client_factory.assert_called_with(self.cmd.cli_ctx, api_version='2025-05-01')
        return self.web_client_factory.return_value.web_apps.begin_create_or_update.call_args.args[2].as_dict()

    def test_create_sends_registry_config_without_runtime_and_with_default_scale(self):
        acr = ('/subscriptions/{}/resourceGroups/rg/providers/Microsoft.ContainerRegistry/registries/myacr'
               .format(_REGISTRY_SUBSCRIPTION))
        image = 'myacr.azurecr.io/app@' + _REGISTRY_DIGEST

        result = create_functionapp(self.cmd, 'rg', 'app', 'sa', flexconsumption_location='eastus',
                                    deployment_image=image, deployment_image_auth_type='SystemAssignedIdentity',
                                    assign_identities=['[system]'], role='AcrPull', scope=acr)

        site = self._created_site()
        self.assertEqual(site['properties']['functionAppConfig'], {
            'deployment': {'storage': {'type': 'Registry', 'value': image,
                                       'authentication': {'type': 'SystemAssignedIdentity'}}},
            'scaleAndConcurrency': {'maximumInstanceCount': 1000, 'instanceMemoryMB': 2048, 'alwaysReady': []}
        })
        # None of the legacy Linux-container markers: container kind, linuxFxVersion or DOCKER_* app settings.
        self.assertEqual(site['kind'], 'functionapp,linux')
        self.assertNotIn('linuxFxVersion', site['properties']['siteConfig'])
        self.assertEqual([setting['name'] for setting in site['properties']['siteConfig']['appSettings']],
                         ['AzureWebJobsStorage'])
        self.runtime_helper.assert_not_called()
        self.prepare_storage.assert_not_called()
        self.prepare_storage_identity.assert_not_called()
        self.create_app_insights.assert_called_once()
        self.assign_identity.assert_called_once_with(self.cmd, 'rg', 'app', ['[system]'], 'AcrPull', None, acr)
        self.get_raw_functionapp.assert_called_once_with(self.cmd.cli_ctx, 'rg', 'app', api_version='2025-05-01')
        self.assertIs(result, self.get_raw_functionapp.return_value)

    def test_create_with_basic_authentication_uses_explicit_scale_settings(self):
        create_functionapp(self.cmd, 'rg', 'app', 'sa', flexconsumption_location='eastus',
                           deployment_image='registry.contoso.com/team/app:v1', deployment_image_auth_type='Basic',
                           deployment_image_username_setting='REGISTRY_USERNAME',
                           deployment_image_password_setting='REGISTRY_PASSWORD',
                           deployment_image_server_url='https://registry.contoso.com',
                           instance_memory=4096, maximum_instance_count=40, always_ready_instances=['http=2'],
                           disable_app_insights='true')

        self.assertEqual(self._created_site()['properties']['functionAppConfig'], {
            'deployment': {'storage': {'type': 'Registry', 'value': 'registry.contoso.com/team/app:v1',
                                       'authentication': {'type': 'Basic', 'usernameSettingName': 'REGISTRY_USERNAME',
                                                          'passwordSettingName': 'REGISTRY_PASSWORD',
                                                          'serverUrl': 'https://registry.contoso.com'}}},
            'scaleAndConcurrency': {'maximumInstanceCount': 40, 'instanceMemoryMB': 4096,
                                    'alwaysReady': [{'name': 'http', 'instanceCount': 2}]}
        })
        self.create_app_insights.assert_not_called()

    def test_create_rejects_conflicting_registry_arguments_before_calling_azure(self):
        registry_args = {'flexconsumption_location': 'eastus', 'deployment_image': 'myacr.azurecr.io/app:v1',
                         'deployment_image_auth_type': 'Anonymous'}
        cases = [
            ('runtime', {'runtime': 'python'}, MutuallyExclusiveArgumentError),
            ('blob deployment storage', {'deployment_storage_name': 'sa2'}, MutuallyExclusiveArgumentError),
            ('legacy registry credentials', {'registry_password': 'password'}, MutuallyExclusiveArgumentError),
            ('container app environment', {'environment': 'env'}, MutuallyExclusiveArgumentError),
            ('missing authentication type', {'deployment_image_auth_type': None}, RequiredArgumentMissingError),
            ('missing image', {'deployment_image': None}, RequiredArgumentMissingError),
            ('not Flex Consumption', {'flexconsumption_location': None, 'plan': 'plan'}, RequiredArgumentMissingError),
        ]
        for case, overrides, error in cases:
            with self.subTest(case), self.assertRaises(error):
                create_functionapp(self.cmd, 'rg', 'app', 'sa', **dict(registry_args, **overrides))
        self.web_client_factory.assert_not_called()


class TestFlexRegistryArgumentParsing(unittest.TestCase):

    def test_registry_arguments_and_aliases_reach_both_commands(self):
        from azure.cli.core.mock import DummyCli
        no_auth_fields = {'deployment_image_identity': None, 'deployment_image_username_setting': None,
                          'deployment_image_password_setting': None, 'deployment_image_server_url': None}
        cases = [
            ('create_functionapp',
             ['functionapp', 'create', '-g', 'rg', '-n', 'app', '-s', 'sa', '--flexconsumption-location', 'eastus',
              '--deployment-image', 'myacr.azurecr.io/app:v1@' + _REGISTRY_DIGEST,
              '--diat', 'userassignedidentity', '--dii', _REGISTRY_IDENTITY],
             dict(no_auth_fields, deployment_image='myacr.azurecr.io/app:v1@' + _REGISTRY_DIGEST,
                  deployment_image_auth_type='UserAssignedIdentity', deployment_image_identity=_REGISTRY_IDENTITY)),
            ('update_deployment_configs',
             ['functionapp', 'deployment', 'config', 'set', '-g', 'rg', '-n', 'app',
              '--deployment-image', 'myacr.azurecr.io/app:v1', '--diat', 'basic', '--dius', 'REGISTRY_USERNAME',
              '--dips', 'REGISTRY_PASSWORD', '--diurl', 'https://myacr.azurecr.io'],
             dict(no_auth_fields, deployment_image='myacr.azurecr.io/app:v1', deployment_image_auth_type='Basic',
                  deployment_image_username_setting='REGISTRY_USERNAME',
                  deployment_image_password_setting='REGISTRY_PASSWORD',
                  deployment_image_server_url='https://myacr.azurecr.io')),
        ]
        for handler, args, expected in cases:
            with self.subTest(handler), \
                    mock.patch('azure.cli.command_modules.appservice.custom.' + handler, autospec=True,
                               return_value={}) as handler_mock, \
                    mock.patch('azure.cli.command_modules.appservice.commands.validate_is_flex_functionapp'):
                self.assertEqual(DummyCli().invoke(args, out_file=io.StringIO()), 0)
                received = handler_mock.call_args.kwargs
                self.assertEqual({key: received[key] for key in expected}, expected)
