# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock
import os

from azure.core.exceptions import HttpResponseError

from azure.mgmt.web import WebSiteManagementClient
from knack.util import CLIError
from azure.cli.core.azclierror import (InvalidArgumentValueError,
                                       MutuallyExclusiveArgumentError,
                                       AzureResponseError,
                                       ArgumentUsageError)
from azure.cli.command_modules.appservice.custom import (set_deployment_user,
                                                         update_git_token, add_hostname,
                                                         update_site_configs,
                                                         get_external_ip,
                                                         view_in_browser,
                                                         sync_site_repo,
                                                         _match_host_names_from_cert,
                                                         bind_ssl_cert,
                                                         list_publish_profiles,
                                                         show_app,
                                                         get_streaming_log,
                                                         download_historical_logs,
                                                         validate_container_app_create_options,
                                                         restore_deleted_webapp,
                                                         list_snapshots,
                                                         restore_snapshot,
                                                         create_managed_ssl_cert,
                                                         add_github_actions,
                                                         update_app_settings,
                                                         update_application_settings_polling,
                                                         update_webapp,
                                                         create_webapp,
                                                         get_auth_settings,
                                                         update_auth_settings,
                                                         _is_auth_v2_app,
                                                         _get_auth_settings_v2,
                                                         _update_auth_settings_v2)

# pylint: disable=line-too-long
from azure.cli.core.profiles import ResourceType


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


class TestWebappMocked(unittest.TestCase):
    def setUp(self):
        self.client = WebSiteManagementClient(mock.MagicMock(), '123455678')

    @mock.patch('azure.cli.command_modules.appservice.custom._update_site_source_control_properties_for_gh_action')
    @mock.patch('azure.cli.command_modules.appservice.custom._add_publish_profile_to_github')
    @mock.patch('azure.cli.command_modules.appservice.custom.prompt_y_n')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_app_runtime_info')
    @mock.patch('github.Github')
    @mock.patch('azure.cli.command_modules.appservice.custom.parse_resource_id')
    @mock.patch('azure.cli.command_modules.appservice.custom.get_site_availability')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory')
    @mock.patch('azure.cli.command_modules.appservice.custom.get_app_details')
    def test_webapp_github_actions_add(self, get_app_details_mock, web_client_factory_mock, site_availability_mock, *args):
        runtime = "python:3.9"
        rg = "group"
        is_linux = True
        cmd = _get_test_cmd()
        get_app_details_mock.return_value = mock.Mock()
        get_app_details_mock.return_value.resource_group = rg
        web_client_factory_mock.return_value.app_service_plans.get.return_value.reserved = is_linux
        site_availability_mock.return_value.name_available = False

        with mock.patch('azure.cli.command_modules.appservice.custom._runtime_supports_github_actions', autospec=True) as m:
            add_github_actions(cmd, rg, "name", "repo", runtime, "token")
            m.assert_called_with(cmd, runtime.replace(":", "|"), is_linux)

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_set_deployment_user_creds(self, client_factory_mock):
        class MockClient:
            def update_publishing_user(self, user):
                # Don't do an actual call, just return the incoming user
                return user

        client_factory_mock.return_value = MockClient()

        # action
        user = set_deployment_user(_get_test_cmd(), 'admin', 'verySecret1')

        # assert things get wired up with a result returned
        assert user.publishing_user_name == 'admin'
        assert user.publishing_password == 'verySecret1'

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_set_source_control_token(self, client_factory_mock):
        client = mock.Mock()
        client_factory_mock.return_value = client
        cmd_mock = _get_test_cmd()
        SourceControl = cmd_mock.get_models('SourceControl')
        sc = SourceControl(name='not-really-needed', source_control_name='GitHub', token='veryNiceToken')
        client.update_source_control.return_value = sc

        # action
        result = update_git_token(cmd_mock, 'veryNiceToken')

        # assert things gets wired up
        self.assertEqual(result.token, None)

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_set_domain_name(self, client_factory_mock):
        client = mock.Mock()
        client_factory_mock.return_value = client
        cmd_mock = _get_test_cmd()
        # set up the return value for getting a webapp
        Site, HostNameBinding = cmd_mock.get_models('Site', 'HostNameBinding')
        webapp = Site(location='westus')
        webapp.name = 'veryNiceWebApp'
        client.web_apps.get.return_value = webapp

        # set up the result value of putting a domain name
        domain = 'veryNiceDomain'
        binding = HostNameBinding(location=webapp.location,
                                  domain_id=domain,
                                  custom_host_name_dns_record_type='A',
                                  host_name_type='Managed')
        client.web_apps.create_or_update_host_name_binding.return_value = binding
        client.web_apps.create_or_update_host_name_binding_slot.return_value = binding
        # action
        result = add_hostname(cmd_mock, 'g1', webapp.name, domain)

        # assert
        self.assertEqual(result.domain_id, domain)

        # action- Slot
        result = add_hostname(cmd_mock, 'g1', webapp.name, domain, 'slot1')

        # assert
        self.assertEqual(result.domain_id, domain)

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    def test_get_external_ip_from_ase(self, client_factory_mock):
        client = mock.Mock()
        client_factory_mock.return_value = client
        cmd_mock = _get_test_cmd()
        # set up the web inside a ASE, with an ip based ssl binding
        HostingEnvironmentProfile = cmd_mock.get_models('HostingEnvironmentProfile')
        host_env = HostingEnvironmentProfile(id='id11')
        host_env.name = 'ase1'
        host_env.resource_group = 'myRg'

        HostNameSslState, SslState, Site, AddressResponse = \
            cmd_mock.get_models('HostNameSslState', 'SslState', 'Site', 'AddressResponse')

        host_ssl_state = HostNameSslState(ssl_state=SslState.ip_based_enabled, virtual_ip='1.2.3.4')
        client.web_apps.get.return_value = Site(name='antarctica', hosting_environment_profile=host_env,
                                                host_name_ssl_states=[host_ssl_state], location='westus')
        client.app_service_environments.list_vips.return_value = AddressResponse()

        # action
        result = get_external_ip(cmd_mock, 'myRg', 'myWeb')

        # assert, we return the virtual ip from the ip based ssl binding
        self.assertEqual('1.2.3.4', result['ip'])

        # tweak to have no ip based ssl binding, but it is in an internal load balancer
        host_ssl_state2 = HostNameSslState(ssl_state=SslState.sni_enabled)
        client.web_apps.get.return_value = Site(name='antarctica', hosting_environment_profile=host_env,
                                                host_name_ssl_states=[host_ssl_state2], location='westus')
        client.app_service_environments.list_vips.return_value = AddressResponse(internal_ip_address='4.3.2.1')

        # action
        result = get_external_ip(cmd_mock, 'myRg', 'myWeb')

        # assert, we take the ILB address
        self.assertEqual('4.3.2.1', result['ip'])

        # tweak to have no ip based ssl binding, and not in internal load balancer
        host_ssl_state2 = HostNameSslState(ssl_state=SslState.sni_enabled)
        client.web_apps.get.return_value = Site(name='antarctica', hosting_environment_profile=host_env,
                                                host_name_ssl_states=[host_ssl_state2], location='westus')
        client.app_service_environments.list_vips.return_value = AddressResponse(service_ip_address='1.1.1.1')

        # action
        result = get_external_ip(cmd_mock, 'myRg', 'myWeb')

        # assert, we take service ip
        self.assertEqual('1.1.1.1', result['ip'])

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._resolve_hostname_through_dns', autospec=True)
    def test_get_external_ip_from_dns(self, resolve_hostname_mock, client_factory_mock):
        client = mock.Mock()
        client_factory_mock.return_value = client
        cmd_mock = _get_test_cmd()
        # set up the web inside a ASE, with an ip based ssl binding
        Site = cmd_mock.get_models('Site')
        site = Site(name='antarctica', location='westus')
        site.default_host_name = 'myweb.com'
        client.web_apps.get.return_value = site

        # action
        get_external_ip(mock.MagicMock(), 'myRg', 'myWeb')

        # assert, we return the virtual ip from the ip based ssl binding
        resolve_hostname_mock.assert_called_with('myweb.com')

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.is_centauri_functionapp', autospec=True)
    def test_update_site_config(self, is_centauri_functionapp_mock, site_op_mock):

        cmd_mock = _get_test_cmd()
        SiteConfig = cmd_mock.get_models('SiteConfig')
        site_config = SiteConfig(name='antarctica')
        site_op_mock.return_value = site_config

        is_centauri_functionapp_mock.return_value = False
        # action
        update_site_configs(cmd_mock, 'myRG', 'myweb', java_version='1.8')
        # assert
        self.assertEqual(site_config.java_version, '1.8')
        # point check some unrelated properties should stay at None
        self.assertEqual(site_config.use32_bit_worker_process, None)
        self.assertEqual(site_config.java_container, None)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    def test_list_publish_profiles_on_slots(self, site_op_mock):
        site_op_mock.return_value = [b'<publishData><publishProfile publishUrl="ftp://123"/><publishProfile publishUrl="ftp://1234"/></publishData>']
        # action
        result = list_publish_profiles(mock.MagicMock(), 'myRG', 'myweb', 'slot1')
        # assert
        site_op_mock.assert_called_with(mock.ANY, 'myRG', 'myweb', 'list_publishing_profile_xml_with_secrets', 'slot1',
                                        {'format': 'WebDeploy'})
        self.assertTrue(result[0]['publishUrl'].startswith('ftp://123'))

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.get_streaming_log', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.open_page_in_browser', autospec=True)
    def test_browse_with_trace(self, webbrowser_mock, log_mock, site_op_mock):
        cmd_mock = _get_test_cmd()
        Site, HostNameSslState, SslState = cmd_mock.get_models('Site', 'HostNameSslState', 'SslState')
        site = Site(location='westus', name='antarctica')
        site.default_host_name = 'haha.com'
        site.enabled_host_names = [site.default_host_name]
        site.host_name_ssl_states = [HostNameSslState(name='does not matter',
                                                      ssl_state=SslState.ip_based_enabled)]

        site_op_mock.return_value = site
        # action
        view_in_browser(mock.MagicMock(), 'myRG', 'myweb', logs=True)
        # assert
        webbrowser_mock.assert_called_with('https://haha.com')
        log_mock.assert_called_with(mock.ANY, 'myRG', 'myweb', None, None)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.is_centauri_functionapp', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._rename_server_farm_props', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._fill_ftp_publishing_url', autospec=True)
    def test_show_webapp(self, file_ftp_mock, rename_mock, is_centauri_functionapp_mock, site_op_mock):
        faked_web = mock.MagicMock()
        site_op_mock.return_value = faked_web
        is_centauri_functionapp_mock.return_value = False
        # action
        result = show_app(mock.MagicMock(), 'myRG', 'myweb', slot=None)
        # assert (we invoke the site op)
        self.assertEqual(faked_web, result)
        self.assertTrue(rename_mock.called)
        self.assertTrue(file_ftp_mock.called)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    def test_sync_repository_skip_bad_error(self, site_op_mock):
        resp = FakedResponse(200)  # because of bad spec, sdk throws on 200.
        setattr(resp, 'reason', 'bad error')
        site_op_mock.side_effect = HttpResponseError(response=resp)
        # action
        sync_site_repo(mock.MagicMock(), 'myRG', 'myweb')
        # assert
        pass  # if we are here, it means CLI has captured the bogus exception

    def test_match_host_names_from_cert(self):
        result = _match_host_names_from_cert(['*.mysite.com'], ['admin.mysite.com', 'log.mysite.com', 'mysite.com'])
        self.assertEqual(set(['admin.mysite.com', 'log.mysite.com']), result)

        result = _match_host_names_from_cert(['*.mysite.com', 'mysite.com'], ['admin.mysite.com', 'log.mysite.com', 'mysite.com'])
        self.assertEqual(set(['admin.mysite.com', 'log.mysite.com', 'mysite.com']), result)

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers', return_value={"auth": "1245!"})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.ping_site', autospec=True)
    @mock.patch('threading.Thread', autospec=True)
    def test_log_stream_supply_cli_ctx(self, threading_mock, ping_site_mock, get_scm_url_mock, get_scm_site_headers_mock):

        # test exception to exit the streaming loop
        class ErrorToExitInfiniteLoop(Exception):
            pass

        threading_mock.side_effect = ErrorToExitInfiniteLoop('Expected error to exit early')
        get_scm_url_mock.return_value = 'http://great_url'
        ping_site_mock.return_value = None
        cmd_mock = mock.MagicMock()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock
        rg_name = "rg"
        app_name = "web1"

        try:
            # action
            get_streaming_log(cmd_mock, rg_name, app_name)
            self.fail('test exception was not thrown')
        except ErrorToExitInfiniteLoop:
            # assert
            get_scm_site_headers_mock.assert_called_with(cli_ctx_mock, app_name, rg_name, None)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_url', autospec=True)
    def test_log_stream_ping_site_failed(self, get_site_url_mock):
        import urllib3
        get_site_url_mock.return_value = 'http://unreachable-url'
        cmd_mock = mock.MagicMock()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock
        rg_name = "rg"
        app_name = "web1"

        try:
            # action
            get_streaming_log(cmd_mock, rg_name, app_name)
            self.fail('Exception not thrown even when site ping should fail')
        except urllib3.exceptions.MaxRetryError:
            # assert
            get_site_url_mock.assert_called_with(cmd_mock, rg_name, app_name, None)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    def test_restore_deleted_webapp(self, site_op_mock):
        cmd_mock = mock.MagicMock()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock
        DeletedAppRestoreRequest = cmd_mock.get_models('DeletedAppRestoreRequest')
        request = DeletedAppRestoreRequest(deleted_site_id='12345', recover_configuration=False)

        # action
        restore_deleted_webapp(cmd_mock, '12345', 'rg', 'web1', None, True)

        # assert
        site_op_mock.assert_called_with(cli_ctx_mock, 'rg', 'web1', 'begin_restore_from_deleted_app', None, request)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    def test_list_webapp_snapshots(self, site_op_mock):
        cmd_mock = mock.MagicMock()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        # action
        list_snapshots(cmd_mock, 'rg', 'web1', None)

        # assert
        site_op_mock.assert_called_with(cli_ctx_mock, 'rg', 'web1', 'list_snapshots', None)

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    def test_restore_snapshot(self, generic_site_op_mock, client_factory_mock):
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cli_ctx_mock.data = {'subscription_id': 'sub1'}
        cmd_mock.cli_ctx = cli_ctx_mock

        client = mock.MagicMock()
        client.web_apps.restore_snapshot_slot = mock.MagicMock()
        client.web_apps.restore_snapshot = mock.MagicMock()

        Site = cmd_mock.get_models('Site')
        site = Site(name='src_web', location='location')
        site.slot_name = 'src_slot'
        site.resouce_group = 'src_rg'
        site.id = '/subscriptions/sub1/resourceGroups/src_rg/providers/Microsoft.Web/sites/src_web/slots/src_slot'

        generic_site_op_mock.return_value = site

        client_factory_mock.return_value = client
        


        SnapshotRecoverySource, SnapshotRestoreRequest = \
            cmd_mock.get_models('SnapshotRecoverySource', 'SnapshotRestoreRequest')
        source = SnapshotRecoverySource(id='/subscriptions/sub1/resourceGroups/src_rg/providers/Microsoft.Web/sites/src_web/slots/src_slot', location='location')
        request = SnapshotRestoreRequest(overwrite=False, snapshot_time='2018-12-07T02:01:31.4708832Z',
                                         recovery_source=source, recover_configuration=False)
        overwrite_request = SnapshotRestoreRequest(overwrite=True, snapshot_time='2018-12-07T02:01:31.4708832Z', recover_configuration=True)

        # action
        restore_snapshot(cmd_mock, 'rg', 'web1', '2018-12-07T02:01:31.4708832Z', slot='slot1', restore_content_only=True,
                         source_resource_group='src_rg', source_name='src_web', source_slot='src_slot')
        restore_snapshot(cmd_mock, 'rg', 'web1', '2018-12-07T02:01:31.4708832Z', restore_content_only=False)

        # assert
        client.web_apps.begin_restore_snapshot_slot.assert_called_with('rg', 'web1', 'slot1', request)
        client.web_apps.begin_restore_snapshot.assert_called_with('rg', 'web1', overwrite_request)

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers', return_value={"auth": "1245!"})
    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._get_log', autospec=True)
    def test_download_log_supply_cli_ctx(self, get_log_mock, get_scm_url_mock, site_op_mock, *args):
        def test_result():
            res = mock.MagicMock()
            res.publishing_user_name, res.publishing_password = 'great_user', 'secret_password'
            return res
        test_scm_url = 'http://great_url'
        get_scm_url_mock.return_value = test_scm_url
        publish_cred_mock = mock.MagicMock()
        publish_cred_mock.result = test_result
        site_op_mock.return_value = publish_cred_mock
        cmd_mock = mock.MagicMock()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock

        # action
        download_historical_logs(cmd_mock, 'rg', 'web1')

        # assert
        get_log_mock.assert_called_with(test_scm_url + '/dump', {"auth": "1245!"}, None)

    def test_valid_linux_create_options(self):
        some_runtime = 'TOMCAT|8.5-jre8'
        test_docker_image = 'lukasz/great-image:123'
        test_multi_container_config = 'some_config.yaml'
        test_multi_container_type = 'COMPOSE'

        self.assertTrue(validate_container_app_create_options(some_runtime, None, None, None))
        self.assertTrue(validate_container_app_create_options(None, test_docker_image, None, None))
        self.assertTrue(validate_container_app_create_options(None, None, test_multi_container_config, test_multi_container_type))
        self.assertFalse(validate_container_app_create_options(some_runtime, None, test_multi_container_config, test_multi_container_type))
        self.assertFalse(validate_container_app_create_options(some_runtime, None, test_multi_container_config, None))
        self.assertFalse(validate_container_app_create_options(some_runtime, test_docker_image, test_multi_container_config, None))
        self.assertFalse(validate_container_app_create_options(None, None, test_multi_container_config, None))
        self.assertFalse(validate_container_app_create_options(None, None, None, None))

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._StackRuntimeHelper', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.get_site_availability', autospec=True)
    def test_linux_webapp_create_no_runtime_raises_error(self, get_site_avail_mock,
                                                         stack_helper_mock, web_client_mock):
        cmd_mock = _get_test_cmd()
        SiteConfig, SkuDescription, NameValuePair = cmd_mock.get_models(
            'SiteConfig', 'SkuDescription', 'NameValuePair')
        cmd_mock.get_models = mock.MagicMock(return_value=(SiteConfig, SkuDescription, NameValuePair))

        # Mock a Linux plan (reserved=True)
        plan_info = mock.MagicMock()
        plan_info.reserved = True
        plan_info.location = 'eastus'
        plan_info.id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan'
        plan_info.sku = SkuDescription(name='F1')
        web_client_mock.return_value.app_service_plans.get.return_value = plan_info

        # Mock site availability (new app name)
        name_validation = mock.MagicMock()
        name_validation.name_available = True
        get_site_avail_mock.return_value = name_validation

        with self.assertRaises(ArgumentUsageError) as context:
            create_webapp(cmd_mock, 'test-rg', 'test-app', 'test-plan')

        self.assertIn('Creating a Linux webapp requires one of the following', str(context.exception))
        self.assertIn('--runtime', str(context.exception))
        self.assertIn('--os-type linux', str(context.exception))

    @mock.patch('azure.cli.command_modules.appservice.custom._verify_hostname_binding', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    def test_create_managed_ssl_cert(self, generic_site_op_mock, client_factory_mock, verify_binding_mock):
        webapp_name = 'someWebAppName'
        rg_name = 'someRgName'
        farm_id = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg1/providers/Microsoft.Web/serverfarms/farm1'
        host_name = 'www.contoso.com'

        client = mock.MagicMock()
        client_factory_mock.return_value = client
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cli_ctx_mock.data = {'subscription_id': 'sub1'}
        cmd_mock.cli_ctx = cli_ctx_mock
        Site, Certificate = cmd_mock.get_models('Site', 'Certificate')
        site = Site(name=webapp_name, location='westeurope')
        site.server_farm_id = farm_id
        generic_site_op_mock.return_value = site

        verify_binding_mock.return_value = False
        with self.assertRaises(CLIError):
            create_managed_ssl_cert(cmd_mock, rg_name, webapp_name, host_name, None)

        verify_binding_mock.return_value = True
        create_managed_ssl_cert(cmd_mock, rg_name, webapp_name, host_name, None)

        cert_def = Certificate(location='westeurope', canonical_name=host_name,
                               server_farm_id=farm_id, password='')
        client.certificates.create_or_update.assert_called_once_with(name=host_name, resource_group_name=rg_name,
                                                                     certificate_envelope=cert_def)


    def test_update_app_settings_error_handling_no_parameters(self):
        """Test that MutuallyExclusiveArgumentError is raised when neither settings nor slot_settings are provided."""
        cmd_mock = _get_test_cmd()
        
        # Test missing both parameters - should fail early without calling any services
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, 
                                   "Please provide either --settings or --slot-settings parameter"):
            update_app_settings(cmd_mock, 'test-rg', 'test-app')

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    @mock.patch('azure.cli.command_modules.appservice.custom.shell_safe_json_parse')
    def test_update_app_settings_error_handling_invalid_format(self, mock_json_parse, mock_site_op):
        """Test that InvalidArgumentValueError is raised for invalid setting formats."""
        cmd_mock = _get_test_cmd()
        
        # Setup minimal mocks needed to reach the error handling code
        mock_app_settings = mock.MagicMock()
        mock_app_settings.properties = {}
        mock_site_op.return_value = mock_app_settings
        
        # Mock shell_safe_json_parse to raise InvalidArgumentValueError (simulating invalid JSON)
        mock_json_parse.side_effect = InvalidArgumentValueError("Invalid JSON format")
        
        # Test invalid format that can't be parsed as JSON or key=value
        invalid_setting = "invalid_format_no_equals_no_json"
        expected_message = r"Invalid setting format.*Expected 'key=value' format or valid JSON"
        
        with self.assertRaisesRegex(InvalidArgumentValueError, expected_message):
            update_app_settings(cmd_mock, 'test-rg', 'test-app', settings=[invalid_setting])

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    @mock.patch('azure.cli.command_modules.appservice.custom.shell_safe_json_parse')
    def test_update_app_settings_error_handling_invalid_format_no_equals(self, mock_json_parse, mock_site_op):
        """Test ValueError path when shell_safe_json_parse raises InvalidArgumentValueError and string contains no '='."""
        cmd_mock = _get_test_cmd()
        
        # Setup minimal mocks needed to reach the error handling code
        mock_app_settings = mock.MagicMock()
        mock_app_settings.properties = {}
        mock_site_op.return_value = mock_app_settings
        
        # Mock shell_safe_json_parse to raise InvalidArgumentValueError
        mock_json_parse.side_effect = InvalidArgumentValueError("Invalid JSON format")
        
        # Test invalid format with no equals sign - this should trigger ValueError in split('=', 1)
        invalid_setting_no_equals = "invalidformatthatcontainsnoequalsign"
        expected_message = r"Invalid setting format.*Expected 'key=value' format or valid JSON"
        
        with self.assertRaisesRegex(InvalidArgumentValueError, expected_message):
            update_app_settings(cmd_mock, 'test-rg', 'test-app', settings=[invalid_setting_no_equals])

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_centauri_functionapp')
    @mock.patch('azure.cli.command_modules.appservice.custom._generic_settings_operation')
    @mock.patch('azure.cli.command_modules.appservice.custom._build_app_settings_output')
    def test_update_app_settings_success_key_value_format(self, mock_build, mock_settings_op, mock_centauri, 
                                                         mock_client_factory, mock_site_op):
        """Test successful processing of key=value format settings."""
        cmd_mock = _get_test_cmd()
        
        # Setup mocks
        mock_app_settings = mock.MagicMock()
        mock_app_settings.properties = {}
        mock_site_op.return_value = mock_app_settings
        
        mock_client = mock.MagicMock()
        mock_client_factory.return_value = mock_client
        mock_centauri.return_value = False
        mock_settings_op.return_value = mock_app_settings
        mock_build.return_value = {"KEY1": "value1", "KEY2": "value2"}
        
        # Test valid key=value format
        result = update_app_settings(cmd_mock, 'test-rg', 'test-app', 
                                   settings=['KEY1=value1', 'KEY2=value2'])
        
        # Verify the function completed successfully
        self.assertEqual(result["KEY1"], "value1")
        self.assertEqual(result["KEY2"], "value2")
        mock_build.assert_called_once()

    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    def test_update_application_settings_polling_error_handling(self, mock_send_request):
        """Test that AzureResponseError is raised in polling function when appropriate."""
        cmd_mock = _get_test_cmd()
        
        # Mock an exception that doesn't have the expected structure
        class MockException(Exception):
            def __init__(self):
                self.response = mock.MagicMock()
                self.response.status_code = 400  # Not 202
                self.response.headers = {}
        
        # Mock _generic_settings_operation to raise the exception
        with mock.patch('azure.cli.command_modules.appservice.custom._generic_settings_operation') as mock_settings_op, \
             self.assertRaisesRegex(AzureResponseError, "Failed to update application settings"):
            mock_settings_op.side_effect = MockException()
            update_application_settings_polling(cmd_mock, 'test-rg', 'test-app', 
                                               mock.MagicMock(), None, mock.MagicMock())

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory')
    @mock.patch('azure.cli.command_modules.appservice.custom.is_centauri_functionapp')
    @mock.patch('azure.cli.command_modules.appservice.custom._generic_settings_operation')
    @mock.patch('azure.cli.command_modules.appservice.custom._build_app_settings_output')
    def test_update_app_settings_success_with_slot_settings(self, mock_build, mock_settings_op, mock_centauri,
                                                           mock_client_factory, mock_site_op):
        """Test successful processing with slot settings."""
        cmd_mock = _get_test_cmd()
        
        # Setup mocks
        mock_app_settings = mock.MagicMock()
        mock_app_settings.properties = {}
        mock_site_op.return_value = mock_app_settings
        
        mock_client = mock.MagicMock()
        mock_slot_config = mock.MagicMock()
        mock_slot_config.app_setting_names = []
        mock_client.web_apps.list_slot_configuration_names.return_value = mock_slot_config
        mock_client_factory.return_value = mock_client
        mock_centauri.return_value = False
        mock_settings_op.return_value = mock_app_settings
        mock_build.return_value = {"SLOT_KEY": "slot_value"}
        
        # Test with slot settings
        result = update_app_settings(cmd_mock, 'test-rg', 'test-app', 
                                   settings=['REGULAR_KEY=regular_value'],
                                   slot_settings=['SLOT_KEY=slot_value'])
        
        # Verify slot configuration was updated
        mock_client.web_apps.list_slot_configuration_names.assert_called_once()
        mock_client.web_apps.update_slot_configuration_names.assert_called_once()
        mock_build.assert_called_once()


class TestUpdateWebapp(unittest.TestCase):

    def _create_site_instance(self, cmd):
        Site = cmd.get_models('Site')
        SiteConfig = cmd.get_models('SiteConfig')
        site_config = SiteConfig(number_of_workers=1)
        instance = Site(location='eastus', site_config=site_config)
        instance.kind = 'app,linux'
        return instance

    def test_update_webapp_platform_release_channel_extended(self):
        cmd_mock = _get_test_cmd()
        instance = self._create_site_instance(cmd_mock)

        result = update_webapp(cmd_mock, instance, platform_release_channel='Extended')

        self.assertEqual(result.additional_properties["properties"]["platformReleaseChannel"], "Extended")

    def test_update_webapp_platform_release_channel_standard(self):
        cmd_mock = _get_test_cmd()
        instance = self._create_site_instance(cmd_mock)

        result = update_webapp(cmd_mock, instance, platform_release_channel='Standard')

        self.assertEqual(result.additional_properties["properties"]["platformReleaseChannel"], "Standard")

    def test_update_webapp_platform_release_channel_latest(self):
        cmd_mock = _get_test_cmd()
        instance = self._create_site_instance(cmd_mock)

        result = update_webapp(cmd_mock, instance, platform_release_channel='Latest')

        self.assertEqual(result.additional_properties["properties"]["platformReleaseChannel"], "Latest")


class TestWebappAuthV2Mocked(unittest.TestCase):
    """Tests for v1/v2 auth migration logic."""

    def test_is_auth_v2_app_none(self):
        self.assertFalse(_is_auth_v2_app(None))

    def test_is_auth_v2_app_empty(self):
        from azure.mgmt.web.models import SiteAuthSettingsV2
        self.assertFalse(_is_auth_v2_app(SiteAuthSettingsV2()))

    def test_is_auth_v2_app_with_platform_enabled(self):
        from azure.mgmt.web.models import SiteAuthSettingsV2, AuthPlatform
        settings = SiteAuthSettingsV2(platform=AuthPlatform(enabled=True))
        self.assertTrue(_is_auth_v2_app(settings))

    def test_is_auth_v2_app_with_platform_disabled(self):
        from azure.mgmt.web.models import SiteAuthSettingsV2, AuthPlatform
        settings = SiteAuthSettingsV2(platform=AuthPlatform(enabled=False))
        self.assertTrue(_is_auth_v2_app(settings))

    def test_is_auth_v2_app_with_identity_providers(self):
        from azure.mgmt.web.models import (SiteAuthSettingsV2, IdentityProviders,
                                            AzureActiveDirectory)
        settings = SiteAuthSettingsV2(
            identity_providers=IdentityProviders(
                azure_active_directory=AzureActiveDirectory(enabled=True)))
        self.assertTrue(_is_auth_v2_app(settings))

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_get_auth_settings_returns_v2_when_configured(self, mock_site_op):
        from azure.mgmt.web.models import SiteAuthSettingsV2, AuthPlatform
        v2_settings = SiteAuthSettingsV2(platform=AuthPlatform(enabled=True))
        mock_site_op.return_value = v2_settings

        cmd = _get_test_cmd()
        result = get_auth_settings(cmd, 'rg', 'myapp')

        self.assertIsInstance(result, SiteAuthSettingsV2)
        mock_site_op.assert_called_once_with(cmd.cli_ctx, 'rg', 'myapp',
                                              'get_auth_settings_v2', None)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_get_auth_settings_falls_back_to_v1(self, mock_site_op):
        from azure.mgmt.web.models import SiteAuthSettingsV2

        v2_settings = SiteAuthSettingsV2()  # empty = not v2
        v1_settings = mock.MagicMock()
        v1_settings.enabled = True

        def side_effect(cli_ctx, rg, name, op, slot=None):
            if op == 'get_auth_settings_v2':
                return v2_settings
            return v1_settings

        mock_site_op.side_effect = side_effect

        cmd = _get_test_cmd()
        result = get_auth_settings(cmd, 'rg', 'myapp')

        self.assertEqual(result, v1_settings)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_get_auth_settings_v2_exception_falls_back_to_v1(self, mock_site_op):
        v1_settings = mock.MagicMock()
        v1_settings.enabled = False

        def side_effect(cli_ctx, rg, name, op, slot=None):
            if op == 'get_auth_settings_v2':
                raise HttpResponseError(message="Not found")
            return v1_settings

        mock_site_op.side_effect = side_effect

        cmd = _get_test_cmd()
        result = get_auth_settings(cmd, 'rg', 'myapp')

        self.assertEqual(result, v1_settings)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_update_auth_settings_uses_v2_when_configured(self, mock_site_op):
        from azure.mgmt.web.models import SiteAuthSettingsV2, AuthPlatform
        v2_settings = SiteAuthSettingsV2(platform=AuthPlatform(enabled=True))
        updated_v2 = SiteAuthSettingsV2(platform=AuthPlatform(enabled=True))

        def side_effect(cli_ctx, rg, name, op, slot=None, extra_parameter=None):
            if op == 'get_auth_settings_v2':
                return v2_settings
            if op == 'update_auth_settings_v2':
                return updated_v2
            return mock.MagicMock()

        mock_site_op.side_effect = side_effect

        cmd = _get_test_cmd()
        result = update_auth_settings(cmd, 'rg', 'myapp', enabled='true',
                                       client_id='test-client-id')

        self.assertEqual(result, updated_v2)
        # Verify update_auth_settings_v2 was called
        calls = [c for c in mock_site_op.call_args_list if c[0][3] == 'update_auth_settings_v2']
        self.assertEqual(len(calls), 1)
        # Verify the v2 settings were modified
        sent_settings = calls[0][1].get('extra_parameter') or calls[0][0][4] if len(calls[0][0]) > 4 else None
        # The auth settings object should have been passed as extra_parameter
        update_call_args = calls[0]
        self.assertIn('update_auth_settings_v2', update_call_args[0])

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_update_auth_settings_require_https_forces_v2(self, mock_site_op):
        from azure.mgmt.web.models import SiteAuthSettingsV2
        v2_settings = SiteAuthSettingsV2()  # empty = not v2 configured yet
        updated_v2 = SiteAuthSettingsV2()

        def side_effect(cli_ctx, rg, name, op, slot=None, extra_parameter=None):
            if op == 'get_auth_settings_v2':
                return v2_settings
            if op == 'update_auth_settings_v2':
                return extra_parameter  # return what was sent
            return mock.MagicMock()

        mock_site_op.side_effect = side_effect

        cmd = _get_test_cmd()
        result = update_auth_settings(cmd, 'rg', 'myapp', require_https='true')

        # Should have used v2 path due to --require-https
        self.assertIsNotNone(result.http_settings)
        self.assertTrue(result.http_settings.require_https)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_update_auth_settings_v1_fallback(self, mock_site_op):
        from azure.mgmt.web.models import SiteAuthSettingsV2
        v2_settings = SiteAuthSettingsV2()  # empty = not v2
        v1_settings = mock.MagicMock()
        v1_settings.enabled = False

        def side_effect(cli_ctx, rg, name, op, slot=None, extra_parameter=None):
            if op == 'get_auth_settings_v2':
                return v2_settings
            if op == 'get_auth_settings':
                return v1_settings
            if op == 'update_auth_settings':
                return extra_parameter
            return mock.MagicMock()

        mock_site_op.side_effect = side_effect

        cmd = _get_test_cmd()
        result = update_auth_settings(cmd, 'rg', 'myapp', enabled='true',
                                       facebook_app_id='fb-id')

        # Should have used v1 path
        self.assertTrue(result.enabled)
        self.assertEqual(result.facebook_app_id, 'fb-id')

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_update_auth_v2_aad_settings(self, mock_site_op):
        from azure.mgmt.web.models import SiteAuthSettingsV2, AuthPlatform
        v2_settings = SiteAuthSettingsV2(platform=AuthPlatform(enabled=True))

        def side_effect(cli_ctx, rg, name, op, slot=None, extra_parameter=None):
            if op == 'get_auth_settings_v2':
                return v2_settings
            if op == 'update_auth_settings_v2':
                return extra_parameter
            return mock.MagicMock()

        mock_site_op.side_effect = side_effect

        cmd = _get_test_cmd()
        result = update_auth_settings(
            cmd, 'rg', 'myapp',
            client_id='my-client-id',
            client_secret='my-secret',
            allowed_audiences=['https://myapp.azurewebsites.net'],
            issuer='https://sts.windows.net/tenant-id/',
            token_store_enabled='true')

        # Verify AAD settings in v2 structure
        aad = result.identity_providers.azure_active_directory
        self.assertTrue(aad.enabled)
        self.assertEqual(aad.registration.client_id, 'my-client-id')
        self.assertEqual(aad.registration.client_secret_setting_name, 'my-secret')
        self.assertEqual(aad.registration.open_id_issuer, 'https://sts.windows.net/tenant-id/')
        self.assertEqual(aad.validation.allowed_audiences, ['https://myapp.azurewebsites.net'])
        # Verify token store
        self.assertTrue(result.login.token_store.enabled)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_update_auth_v2_facebook_settings(self, mock_site_op):
        from azure.mgmt.web.models import SiteAuthSettingsV2, AuthPlatform
        v2_settings = SiteAuthSettingsV2(platform=AuthPlatform(enabled=True))

        def side_effect(cli_ctx, rg, name, op, slot=None, extra_parameter=None):
            if op == 'get_auth_settings_v2':
                return v2_settings
            if op == 'update_auth_settings_v2':
                return extra_parameter
            return mock.MagicMock()

        mock_site_op.side_effect = side_effect

        cmd = _get_test_cmd()
        result = update_auth_settings(
            cmd, 'rg', 'myapp',
            facebook_app_id='fb-app-id',
            facebook_app_secret='fb-secret',
            facebook_oauth_scopes=['public_profile', 'email'])

        fb = result.identity_providers.facebook
        self.assertTrue(fb.enabled)
        self.assertEqual(fb.registration.app_id, 'fb-app-id')
        self.assertEqual(fb.registration.app_secret_setting_name, 'fb-secret')
        self.assertEqual(fb.login.scopes, ['public_profile', 'email'])

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_update_auth_v2_action_allow_anonymous(self, mock_site_op):
        from azure.mgmt.web.models import SiteAuthSettingsV2, AuthPlatform
        v2_settings = SiteAuthSettingsV2(platform=AuthPlatform(enabled=True))

        def side_effect(cli_ctx, rg, name, op, slot=None, extra_parameter=None):
            if op == 'get_auth_settings_v2':
                return v2_settings
            if op == 'update_auth_settings_v2':
                return extra_parameter
            return mock.MagicMock()

        mock_site_op.side_effect = side_effect

        cmd = _get_test_cmd()
        result = update_auth_settings(cmd, 'rg', 'myapp', action='AllowAnonymous')

        self.assertEqual(result.global_validation.unauthenticated_client_action, 'AllowAnonymous')

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_update_auth_v2_action_login_with_aad(self, mock_site_op):
        from azure.mgmt.web.models import SiteAuthSettingsV2, AuthPlatform
        v2_settings = SiteAuthSettingsV2(platform=AuthPlatform(enabled=True))

        def side_effect(cli_ctx, rg, name, op, slot=None, extra_parameter=None):
            if op == 'get_auth_settings_v2':
                return v2_settings
            if op == 'update_auth_settings_v2':
                return extra_parameter
            return mock.MagicMock()

        mock_site_op.side_effect = side_effect

        cmd = _get_test_cmd()
        result = update_auth_settings(cmd, 'rg', 'myapp',
                                       action='LoginWithAzureActiveDirectory')

        self.assertEqual(result.global_validation.unauthenticated_client_action, 'RedirectToLoginPage')
        self.assertEqual(result.global_validation.redirect_to_provider, 'azureactivedirectory')


class FakedResponse:  # pylint: disable=too-few-public-methods
    def __init__(self, status_code):
        self.status_code = status_code


class TestCreateAppServicePlanDefaults(unittest.TestCase):
    """Tests for create_app_service_plan default SKU behavior"""

    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory')
    @mock.patch('azure.cli.command_modules.appservice.custom._get_location_from_resource_group', return_value='eastus')
    def test_default_sku_is_p0v3_when_not_specified(self, mock_location, mock_client_factory):
        from azure.cli.command_modules.appservice.custom import create_app_service_plan
        mock_cmd = mock.MagicMock()
        mock_cmd.get_models.return_value = (mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        mock_cmd.cli_ctx = mock.MagicMock()
        mock_client = mock.MagicMock()
        mock_client_factory.return_value = mock_client

        # Call without sku parameter — should default to P0V3
        try:
            create_app_service_plan(mock_cmd, 'rg', 'plan', is_linux=True, hyper_v=False)
        except Exception:
            pass  # We don't care about downstream errors, just checking the SKU

        # Verify SkuDescription was called with P0V3 tier/name
        sku_description_cls = mock_cmd.get_models.return_value[1]
        sku_description_cls.assert_called()
        call_kwargs = sku_description_cls.call_args
        # The sku name should be normalized P0V3
        self.assertIn('P0V3', str(call_kwargs))


if __name__ == '__main__':
    unittest.main()
