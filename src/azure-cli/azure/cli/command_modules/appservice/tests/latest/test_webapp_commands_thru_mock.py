# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock
import os

from msrestazure.azure_exceptions import CloudError

from azure.mgmt.web import WebSiteManagementClient
from knack.util import CLIError
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
                                                         add_github_actions)

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
        setattr(resp, 'text', '{"Message": ""}')
        site_op_mock.side_effect = CloudError(resp, error="bad error")
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
    def test_restore_snapshot(self, client_factory_mock):
        cmd_mock = _get_test_cmd()
        cli_ctx_mock = mock.MagicMock()
        cli_ctx_mock.data = {'subscription_id': 'sub1'}
        cmd_mock.cli_ctx = cli_ctx_mock

        client = mock.MagicMock()
        client.web_apps.restore_snapshot_slot = mock.MagicMock()
        client.web_apps.restore_snapshot = mock.MagicMock()
        client_factory_mock.return_value = client

        SnapshotRecoverySource, SnapshotRestoreRequest = \
            cmd_mock.get_models('SnapshotRecoverySource', 'SnapshotRestoreRequest')
        source = SnapshotRecoverySource(id='/subscriptions/sub1/resourceGroups/src_rg/providers/Microsoft.Web/sites/src_web/slots/src_slot')
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


class FakedResponse(object):  # pylint: disable=too-few-public-methods
    def __init__(self, status_code):
        self.status_code = status_code


if __name__ == '__main__':
    unittest.main()
