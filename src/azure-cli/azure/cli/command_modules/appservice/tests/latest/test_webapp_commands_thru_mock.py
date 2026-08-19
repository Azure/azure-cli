# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock
import os
import types
from collections.abc import Mapping

from azure.core.exceptions import HttpResponseError

from azure.mgmt.web import WebSiteManagementClient
from knack.util import CLIError
from azure.cli.core.azclierror import (InvalidArgumentValueError,
                                       MutuallyExclusiveArgumentError,
                                       ArgumentUsageError,
                                       AzureResponseError,
                                       ResourceNotFoundError)
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
                                                         list_startup_logs,
                                                         show_startup_log,
                                                         troubleshoot_status,
                                                         create_webapp)
from azure.cli.command_modules.appservice.utils import _rename_server_farm_props, get_site_server_farm_id
from azure.cli.command_modules.appservice.commands import (transform_rename_server_farm_id,
                                                            transform_rename_server_farm_id_list)

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

    def test_transform_rename_server_farm_id_renames_key(self):
        # Verifies the post-serialisation transformer adds appServicePlanId alongside serverFarmId
        farm_id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan'
        web = {
            'location': 'westus',
            'serverFarmId': farm_id,
        }

        result = transform_rename_server_farm_id(web)

        self.assertEqual(result['appServicePlanId'], farm_id)
        # serverFarmId is preserved for backward compatibility
        self.assertEqual(result['serverFarmId'], farm_id)

    def test_transform_rename_server_farm_id_nested_under_properties(self):
        # New SDK ARM-envelope layout: serverFarmId is under 'properties', not at the top level
        farm_id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan'
        web = {
            'location': 'westus',
            'properties': {
                'serverFarmId': farm_id,
                'name': 'myapp',
            },
        }

        result = transform_rename_server_farm_id(web)

        self.assertEqual(result['appServicePlanId'], farm_id)
        # serverFarmId is preserved in properties for backward compatibility
        self.assertEqual(result['properties']['serverFarmId'], farm_id)

    def test_transform_rename_server_farm_id_model_object(self):
        # When the transformer receives a raw model object (before todict), it must
        # serialise the object first and then add appServicePlanId.
        farm_id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan'
        # Simulate a model object with __dict__ that todict() will expand.
        # Note: attribute names with underscores are converted to camelCase by todict(),
        # so set them as camelCase to match what todict() would produce.
        web_obj = types.SimpleNamespace(location='westus')
        web_obj.__dict__['serverFarmId'] = farm_id

        with mock.patch('azure.cli.core.util.todict', return_value={'location': 'westus', 'serverFarmId': farm_id}):
            result = transform_rename_server_farm_id(web_obj)

        self.assertEqual(result['appServicePlanId'], farm_id)
        # serverFarmId is preserved for backward compatibility
        self.assertEqual(result['serverFarmId'], farm_id)

    def test_transform_rename_server_farm_id_noop_when_already_renamed(self):
        farm_id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan'
        web = {'appServicePlanId': farm_id}

        result = transform_rename_server_farm_id(web)

        self.assertEqual(result['appServicePlanId'], farm_id)
        self.assertNotIn('serverFarmId', result)

    def test_transform_rename_server_farm_id_list(self):
        farm_id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan'
        webs = [
            {'serverFarmId': farm_id, 'name': 'app1'},
            {'appServicePlanId': farm_id, 'name': 'app2'},
        ]

        results = transform_rename_server_farm_id_list(webs)

        for r in results:
            self.assertEqual(r['appServicePlanId'], farm_id)

    def test_rename_server_farm_props_handles_object_attributes(self):
        site = types.SimpleNamespace(
            server_farm_id='/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan')

        _rename_server_farm_props(site)

        self.assertEqual(site.app_service_plan_id,
                         '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Web/serverfarms/plan')
        self.assertFalse(hasattr(site, 'server_farm_id'))

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
        SourceControl, SourceControlProperties = cmd_mock.get_models('SourceControl', 'SourceControlProperties')
        sc = SourceControl(properties=SourceControlProperties(token='veryNiceToken'))
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
        binding = HostNameBinding(domain_id=domain,
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
        site_config = SiteConfig()
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

    @mock.patch('azure.cli.command_modules.appservice.custom.is_flex_functionapp', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._verify_hostname_binding', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom.web_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation', autospec=True)
    def test_create_managed_ssl_cert(self, generic_site_op_mock, client_factory_mock, verify_binding_mock, is_flex_mock):
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
        is_flex_mock.return_value = False

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

        self.assertEqual(result.properties["platformReleaseChannel"], "Extended")

    def test_update_webapp_platform_release_channel_standard(self):
        cmd_mock = _get_test_cmd()
        instance = self._create_site_instance(cmd_mock)

        result = update_webapp(cmd_mock, instance, platform_release_channel='Standard')

        self.assertEqual(result.properties["platformReleaseChannel"], "Standard")

    def test_update_webapp_platform_release_channel_latest(self):
        cmd_mock = _get_test_cmd()
        instance = self._create_site_instance(cmd_mock)

        result = update_webapp(cmd_mock, instance, platform_release_channel='Latest')

        self.assertEqual(result.properties["platformReleaseChannel"], "Latest")


class TestStartupLogsMocked(unittest.TestCase):
    """Tests for az webapp log startup list/show commands."""

    def setUp(self):
        # Default: pretend the app is Linux so existing tests exercise the happy path.
        # Individual tests can re-patch these when they need different behavior.
        is_linux_patch = mock.patch(
            'azure.cli.command_modules.appservice.custom.is_linux_webapp',
            return_value=True)
        client_factory_patch = mock.patch(
            'azure.cli.command_modules.appservice.custom.web_client_factory')
        is_linux_patch.start()
        client_factory_patch.start()
        self.addCleanup(is_linux_patch.stop)
        self.addCleanup(client_factory_patch.stop)

    def _make_response(self, status_code=200, json_data=None, text='', headers=None, reason=''):
        resp = mock.MagicMock()
        resp.status_code = status_code
        resp.reason = reason
        resp.text = text
        resp.headers = headers or {}
        resp.json.return_value = json_data
        return resp

    # ---- list_startup_logs ----

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_list_startup_logs_success(self, requests_get_mock, _scm_url_mock, _headers_mock):
        files = [
            {'Filename': '2026_04_13_lw0sdlwk000002_success.log', 'Href': '/api/startuplogs/...'},
            {'Filename': '2026_04_13_lw0sdlwk000003_failure.log', 'Href': '/api/startuplogs/...'},
        ]
        requests_get_mock.return_value = self._make_response(200, json_data={'files': files})

        result = list_startup_logs(_get_test_cmd(), 'myRG', 'myApp')

        self.assertEqual(result, files)
        requests_get_mock.assert_called_once_with(
            'https://myapp.scm.azurewebsites.net/api/startuplogs',
            headers={'Authorization': 'Bearer token'},
            params={}
        )

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_list_startup_logs_with_filters(self, requests_get_mock, _scm_url_mock, _headers_mock):
        requests_get_mock.return_value = self._make_response(200, json_data={'files': []})

        list_startup_logs(_get_test_cmd(), 'myRG', 'myApp', outcome='failure', instance='lw0sdlwk000002')

        requests_get_mock.assert_called_once_with(
            'https://myapp.scm.azurewebsites.net/api/startuplogs',
            headers={'Authorization': 'Bearer token'},
            params={'type': 'failure', 'instance': 'lw0sdlwk000002'}
        )

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_list_startup_logs_404_graceful(self, requests_get_mock, _scm_url_mock, _headers_mock):
        requests_get_mock.return_value = self._make_response(404)

        with mock.patch('azure.cli.command_modules.appservice.custom.logger') as logger_mock:
            result = list_startup_logs(_get_test_cmd(), 'myRG', 'myApp')

        self.assertEqual(result, [])
        logger_mock.warning.assert_called_once()
        self.assertIn('platform version', logger_mock.warning.call_args[0][0])

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_list_startup_logs_500_raises(self, requests_get_mock, _scm_url_mock, _headers_mock):
        requests_get_mock.return_value = self._make_response(500, reason='Internal Server Error')

        with self.assertRaises(CLIError) as cm:
            list_startup_logs(_get_test_cmd(), 'myRG', 'myApp')
        self.assertIn('500', str(cm.exception))

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_list_startup_logs_with_slot(self, requests_get_mock, scm_url_mock, _headers_mock):
        requests_get_mock.return_value = self._make_response(200, json_data={'files': []})

        list_startup_logs(_get_test_cmd(), 'myRG', 'myApp', slot='staging')

        scm_url_mock.assert_called_once_with(mock.ANY, 'myRG', 'myApp', 'staging')

    # ---- show_startup_log ----

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_show_startup_log_latest(self, requests_get_mock, _scm_url_mock, _headers_mock):
        log_text = 'Container started successfully.\nListening on port 8080.'
        requests_get_mock.return_value = self._make_response(
            200, text=log_text,
            headers={
                'Content-Type': 'text/plain',
                'X-StartupLog-Filename': '2026_04_13_lw0_success.log',
                'X-StartupLog-Date': '2026-04-13T10:00:00Z',
                'X-StartupLog-Instance': 'lw0sdlwk000002',
                'X-StartupLog-Outcome': 'success',
            }
        )

        result = show_startup_log(_get_test_cmd(), 'myRG', 'myApp')

        self.assertEqual(result['content'], log_text)
        self.assertEqual(result['filename'], '2026_04_13_lw0_success.log')
        self.assertEqual(result['instance'], 'lw0sdlwk000002')
        self.assertEqual(result['outcome'], 'success')
        requests_get_mock.assert_called_once_with(
            'https://myapp.scm.azurewebsites.net/api/startuplogs?latest=true',
            headers={'Authorization': 'Bearer token'}
        )

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_show_startup_log_specific_filename(self, requests_get_mock, _scm_url_mock, _headers_mock):
        requests_get_mock.return_value = self._make_response(
            200, text='log content',
            headers={'Content-Type': 'text/plain'}
        )

        show_startup_log(_get_test_cmd(), 'myRG', 'myApp', filename='2026_04_13_lw0_success.log')

        requests_get_mock.assert_called_once_with(
            'https://myapp.scm.azurewebsites.net/api/startuplogs/2026_04_13_lw0_success.log',
            headers={'Authorization': 'Bearer token'}
        )

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_show_startup_log_with_instance(self, requests_get_mock, _scm_url_mock, _headers_mock):
        requests_get_mock.return_value = self._make_response(
            200, text='instance log content',
            headers={
                'Content-Type': 'text/plain',
                'X-StartupLog-Filename': '2026_04_13_lw0sdlwk000002_failure.log',
                'X-StartupLog-Instance': 'lw0sdlwk000002',
                'X-StartupLog-Outcome': 'failure',
            }
        )

        result = show_startup_log(_get_test_cmd(), 'myRG', 'myApp', instance='lw0sdlwk000002')

        self.assertEqual(result['content'], 'instance log content')
        self.assertEqual(result['instance'], 'lw0sdlwk000002')
        requests_get_mock.assert_called_once_with(
            'https://myapp.scm.azurewebsites.net/api/startuplogs?latest=true&instance=lw0sdlwk000002',
            headers={'Authorization': 'Bearer token'}
        )

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_show_startup_log_404_no_filename(self, requests_get_mock, _scm_url_mock, _headers_mock):
        requests_get_mock.return_value = self._make_response(404)

        with mock.patch('azure.cli.command_modules.appservice.custom.logger') as logger_mock:
            result = show_startup_log(_get_test_cmd(), 'myRG', 'myApp')

        self.assertIsNone(result)
        self.assertIn('platform version', logger_mock.warning.call_args[0][0])

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_show_startup_log_404_with_filename(self, requests_get_mock, _scm_url_mock, _headers_mock):
        requests_get_mock.return_value = self._make_response(404)

        with mock.patch('azure.cli.command_modules.appservice.custom.logger') as logger_mock:
            result = show_startup_log(_get_test_cmd(), 'myRG', 'myApp', filename='nonexistent.log')

        self.assertIsNone(result)
        self.assertIn('nonexistent.log', logger_mock.warning.call_args[0][1])

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_show_startup_log_500_raises(self, requests_get_mock, _scm_url_mock, _headers_mock):
        requests_get_mock.return_value = self._make_response(500, reason='Internal Server Error')

        with self.assertRaises(CLIError) as cm:
            show_startup_log(_get_test_cmd(), 'myRG', 'myApp')
        self.assertIn('500', str(cm.exception))

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_show_startup_log_json_response(self, requests_get_mock, _scm_url_mock, _headers_mock):
        json_data = {'filename': 'test.log', 'content': 'data'}
        requests_get_mock.return_value = self._make_response(
            200, json_data=json_data,
            headers={'Content-Type': 'application/json'}
        )

        result = show_startup_log(_get_test_cmd(), 'myRG', 'myApp')

        self.assertEqual(result, json_data)

    # ---- Linux-only gating ----

    def test_list_startup_logs_raises_on_windows(self):
        with mock.patch('azure.cli.command_modules.appservice.custom.is_linux_webapp',
                        return_value=False):
            with self.assertRaises(ArgumentUsageError) as cm:
                list_startup_logs(_get_test_cmd(), 'myRG', 'myWindowsApp')
        self.assertIn('Linux', str(cm.exception))

    def test_show_startup_log_raises_on_windows(self):
        with mock.patch('azure.cli.command_modules.appservice.custom.is_linux_webapp',
                        return_value=False):
            with self.assertRaises(ArgumentUsageError) as cm:
                show_startup_log(_get_test_cmd(), 'myRG', 'myWindowsApp')
        self.assertIn('Linux', str(cm.exception))

    # ---- --filename / --instance mutual exclusion ----

    def test_show_startup_log_filename_and_instance_mutually_exclusive(self):
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            show_startup_log(_get_test_cmd(), 'myRG', 'myApp',
                             filename='2026_04_13_lw0_success.log',
                             instance='lw0sdlwk000002')
        self.assertIn('--filename', str(cm.exception))
        self.assertIn('--instance', str(cm.exception))

    # ---- 404 disambiguation when --instance is set ----

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_list_startup_logs_404_with_instance(self, requests_get_mock, _scm_url_mock, _headers_mock):
        requests_get_mock.return_value = self._make_response(404)

        with mock.patch('azure.cli.command_modules.appservice.custom.logger') as logger_mock:
            result = list_startup_logs(_get_test_cmd(), 'myRG', 'myApp', instance='lw0sdlwk000002')

        self.assertEqual(result, [])
        logger_mock.warning.assert_called_once()
        self.assertIn('instance', logger_mock.warning.call_args[0][0])
        self.assertEqual(logger_mock.warning.call_args[0][1], 'lw0sdlwk000002')

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('requests.get')
    def test_show_startup_log_404_with_instance(self, requests_get_mock, _scm_url_mock, _headers_mock):
        requests_get_mock.return_value = self._make_response(404)

        with mock.patch('azure.cli.command_modules.appservice.custom.logger') as logger_mock:
            result = show_startup_log(_get_test_cmd(), 'myRG', 'myApp', instance='lw0sdlwk000002')

        self.assertIsNone(result)
        logger_mock.warning.assert_called_once()
        self.assertIn('instance', logger_mock.warning.call_args[0][0])
        self.assertEqual(logger_mock.warning.call_args[0][1], 'lw0sdlwk000002')


class TestTroubleshootStatusMocked(unittest.TestCase):
    """Tests for az webapp troubleshoot status (ARM siteStatus + SCM startuplogs/summary)."""

    def setUp(self):
        is_linux_patch = mock.patch(
            'azure.cli.command_modules.appservice.custom.is_linux_webapp',
            return_value=True)
        client_factory_patch = mock.patch(
            'azure.cli.command_modules.appservice.custom.web_client_factory')
        sub_id_patch = mock.patch(
            'azure.cli.core.commands.client_factory.get_subscription_id',
            return_value='00000000-0000-0000-0000-000000000000')
        self.client_factory_mock = client_factory_patch.start()
        is_linux_patch.start()
        sub_id_patch.start()
        self.addCleanup(is_linux_patch.stop)
        self.addCleanup(client_factory_patch.stop)
        self.addCleanup(sub_id_patch.stop)
        # troubleshoot_status pins to API version '2024-11-01' explicitly, so the
        # SDK config value here just needs to be set to avoid a MagicMock leaking
        # into unrelated call sites; it is not what shows up in the assertion URLs.
        self.client_factory_mock.return_value._config.api_version = '2024-11-01'

        self.cmd = _get_test_cmd()
        self.cmd.cli_ctx.cloud.endpoints.resource_manager = 'https://management.azure.com'

    @staticmethod
    def _arm_response(items):
        return {'properties': items}

    @staticmethod
    def _instances_payload(mapping):
        """Build an ARM /instances response from {hex_id: machineName} mapping."""
        return {'value': [{'name': hex_id, 'properties': {'machineName': mn}}
                          for hex_id, mn in mapping.items()]}

    @staticmethod
    def _make_response(status_code=200, json_data=None, reason='', text=''):
        resp = mock.MagicMock()
        resp.status_code = status_code
        resp.reason = reason
        resp.text = text
        resp.json.return_value = json_data
        return resp

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    @mock.patch('requests.get')
    def test_troubleshoot_status_all_instances(self, requests_get_mock, send_raw_request_mock,
                                               _scm_url_mock, _headers_mock):
        arm_items = [
            {'instanceId': 'a3f1b', 'state': 'Started', 'action': 'SiteStarted',
             'lastError': None, 'lastErrorDetails': None, 'lastErrorTimestamp': None,
             'details': 'Site is running', 'detailsLevel': 'Information'},
            {'instanceId': 'b4d22', 'state': 'Starting', 'action': 'PullingImage',
             'lastError': None, 'lastErrorDetails': None, 'lastErrorTimestamp': None,
             'details': 'Pulling image', 'detailsLevel': 'Warning'},
        ]
        send_raw_request_mock.side_effect = [
            mock.MagicMock(json=mock.MagicMock(return_value=self._instances_payload(
                {'a3f1b': 'lw0sdlwk0008PB', 'b4d22': 'lw1sdlwk0009EF'}))),
            mock.MagicMock(json=mock.MagicMock(return_value=self._arm_response(arm_items))),
        ]
        # Real KuduLite response is a single list with one entry per instance.
        a3f1b_startup = {'Succeeded': 1, 'Failed': 0}
        b4d22_startup = {'Succeeded': 0, 'Failed': 3}
        requests_get_mock.return_value = self._make_response(200, json_data=[
            {'InstanceId': 'lw0sdlwk0008PB', 'Startup': a3f1b_startup},
            {'InstanceId': 'lw1sdlwk0009EF', 'Startup': b4d22_startup},
        ])

        result = troubleshoot_status(self.cmd, 'myRG', 'myApp')

        self.assertEqual(result['instances'][0]['startup'], a3f1b_startup)
        self.assertEqual(result['instances'][1]['startup'], b4d22_startup)
        self.assertEqual(result['instances'][0]['machineName'], 'lw0sdlwk0008PB')
        self.assertEqual(result['instances'][1]['machineName'], 'lw1sdlwk0009EF')
        # ARM calls: instances FIRST (so we can resolve --instance), then siteStatus.
        arm_urls = [call.args[2] for call in send_raw_request_mock.call_args_list]
        self.assertEqual(arm_urls, [
            'https://management.azure.com/subscriptions/00000000-0000-0000-0000-000000000000'
            '/resourceGroups/myRG/providers/Microsoft.Web/sites/myApp/instances?api-version=2024-11-01',
            'https://management.azure.com/subscriptions/00000000-0000-0000-0000-000000000000'
            '/resourceGroups/myRG/providers/Microsoft.Web/sites/myApp/siteStatus?api-version=2024-11-01',
        ])
        # Single unfiltered SCM call returns every instance in one response.
        requests_get_mock.assert_called_once_with(
            'https://myapp.scm.azurewebsites.net/api/startuplogs/summary',
            headers={'Authorization': 'Bearer token'},
            timeout=30,
        )

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    @mock.patch('requests.get')
    def test_troubleshoot_status_single_instance(self, requests_get_mock, send_raw_request_mock,
                                                 _scm_url_mock, _headers_mock):
        arm_item = {'instanceId': '7c2d9', 'state': 'Stopped', 'action': 'SiteStopped',
                    'lastError': 'NoResponse', 'lastErrorDetails': 'Worker not reachable',
                    'lastErrorTimestamp': '2026-05-20T18:50:44Z',
                    'details': 'Stopped', 'detailsLevel': 'Error'}
        send_raw_request_mock.side_effect = [
            mock.MagicMock(json=mock.MagicMock(return_value=self._instances_payload(
                {'7c2d9': 'lw0sdlwk0007AB'}))),
            mock.MagicMock(json=mock.MagicMock(return_value=self._arm_response(arm_item))),
        ]
        startup_summary = {'Succeeded': 0, 'Failed': 4}
        requests_get_mock.return_value = self._make_response(
            200, json_data=[{'InstanceId': 'lw0sdlwk0007AB', 'Startup': startup_summary}])

        result = troubleshoot_status(self.cmd, 'myRG', 'myApp', instance='7c2d9')

        self.assertEqual(result['instances'][0]['instanceId'], '7c2d9')
        self.assertEqual(result['instances'][0]['startup'], startup_summary)
        self.assertEqual(result['instances'][0]['machineName'], 'lw0sdlwk0007AB')
        arm_urls = [call.args[2] for call in send_raw_request_mock.call_args_list]
        self.assertEqual(arm_urls, [
            'https://management.azure.com/subscriptions/00000000-0000-0000-0000-000000000000'
            '/resourceGroups/myRG/providers/Microsoft.Web/sites/myApp/instances?api-version=2024-11-01',
            'https://management.azure.com/subscriptions/00000000-0000-0000-0000-000000000000'
            '/resourceGroups/myRG/providers/Microsoft.Web/sites/myApp/siteStatus/7c2d9'
            '?api-version=2024-11-01',
        ])
        requests_get_mock.assert_called_once_with(
            'https://myapp.scm.azurewebsites.net/api/startuplogs/summary?instance=lw0sdlwk0007AB',
            headers={'Authorization': 'Bearer token'},
            timeout=30,
        )

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    @mock.patch('requests.get')
    def test_troubleshoot_status_summary_404_returns_empty_startup(
            self, requests_get_mock, send_raw_request_mock, _scm_url_mock, _headers_mock):
        arm_items = [{'instanceId': 'abcde', 'state': 'Started', 'action': 'SiteStarted'}]
        send_raw_request_mock.side_effect = [
            mock.MagicMock(json=mock.MagicMock(return_value=self._instances_payload(
                {'abcde': 'lw0sdlwk0001AA'}))),
            mock.MagicMock(json=mock.MagicMock(return_value=self._arm_response(arm_items))),
        ]
        requests_get_mock.return_value = self._make_response(404)

        result = troubleshoot_status(self.cmd, 'myRG', 'myApp')

        # A 404 from the /api/startuplogs/summary endpoint means the KuduLite
        # build doesn't recognize the route yet (feature not rolled out).
        # Surface that as a SummaryFetchStatus so users aren't misled into
        # thinking their site had no startup attempts.
        startup = result['instances'][0]['startup']
        self.assertIsNotNone(startup)
        self.assertIn('Startup summary is not available for this app', startup.get('SummaryFetchStatus', ''))
        self.assertIn("not rolled out to your app's region yet", startup.get('SummaryFetchStatus', ''))

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': '******'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    @mock.patch('requests.get')
    def test_troubleshoot_status_summary_400_invalid_filename_surfaces_message(
            self, requests_get_mock, send_raw_request_mock, _scm_url_mock, _headers_mock):
        # Older KuduLite build routes /api/startuplogs/{filename} and has no
        # /summary sub-route, so it returns 400 "Invalid startup log filename."
        # This should surface as feature-not-available, not as "no startups".
        arm_items = [{'instanceId': 'abcde', 'state': 'Started', 'action': 'SiteStarted'}]
        send_raw_request_mock.side_effect = [
            mock.MagicMock(json=mock.MagicMock(return_value=self._instances_payload(
                {'abcde': 'lw0sdlwk0001AA'}))),
            mock.MagicMock(json=mock.MagicMock(return_value=self._arm_response(arm_items))),
        ]
        requests_get_mock.return_value = self._make_response(
            400, reason='BadRequest', text='Invalid startup log filename.')

        result = troubleshoot_status(self.cmd, 'myRG', 'myApp')

        startup = result['instances'][0]['startup']
        self.assertIsNotNone(startup)
        msg = startup.get('SummaryFetchStatus', '')
        self.assertIn('Startup summary is not available for this app', msg)
        self.assertIn("not rolled out to your app's region yet", msg)

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': '******'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    @mock.patch('requests.get')
    def test_troubleshoot_status_summary_request_exception_surfaces_transport_error(
            self, requests_get_mock, send_raw_request_mock, _scm_url_mock, _headers_mock):
        # Regression: when requests.get raises a transport-level exception
        # (ConnectionError, timeout, TLS failure) the previous code left
        # SummaryFetchStatus unset, so callers couldn't tell whether SCM was
        # simply healthy-with-no-startups or unreachable. Ensure we surface a
        # meaningful message including the exception class.
        import requests as _requests
        arm_items = [{'instanceId': 'abcde', 'state': 'Started', 'action': 'SiteStarted'}]
        send_raw_request_mock.side_effect = [
            mock.MagicMock(json=mock.MagicMock(return_value=self._instances_payload(
                {'abcde': 'lw0sdlwk0001AA'}))),
            mock.MagicMock(json=mock.MagicMock(return_value=self._arm_response(arm_items))),
        ]
        requests_get_mock.side_effect = _requests.ConnectionError('boom')

        result = troubleshoot_status(self.cmd, 'myRG', 'myApp')

        startup = result['instances'][0]['startup']
        self.assertIsNotNone(startup)
        msg = startup.get('SummaryFetchStatus', '')
        self.assertIn('Failed to reach SCM startup summary endpoint', msg)
        self.assertIn('ConnectionError', msg)

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    def test_troubleshoot_status_arm_404_with_instance(self, send_raw_request_mock,
                                                      _scm_url_mock, _headers_mock):
        error = HttpResponseError(message='Not found')
        error.status_code = 404
        send_raw_request_mock.side_effect = error

        with self.assertRaises(ResourceNotFoundError):
            troubleshoot_status(self.cmd, 'myRG', 'myApp', instance='7c2d9')

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    @mock.patch('requests.get')
    def test_troubleshoot_status_summary_500_surfaces_message(
            self, requests_get_mock, send_raw_request_mock, _scm_url_mock, _headers_mock):
        arm_items = [{'instanceId': 'abcde', 'state': 'Started', 'action': 'SiteStarted'}]
        send_raw_request_mock.side_effect = [
            mock.MagicMock(json=mock.MagicMock(return_value=self._instances_payload(
                {'abcde': 'lw0sdlwk0001AA'}))),
            mock.MagicMock(json=mock.MagicMock(return_value=self._arm_response(arm_items))),
        ]
        requests_get_mock.return_value = self._make_response(500, reason='Internal Server Error')

        result = troubleshoot_status(self.cmd, 'myRG', 'myApp')

        # Non-200 -> feature-not-available message, not silent drop.
        startup = result['instances'][0]['startup']
        self.assertIsNotNone(startup)
        self.assertIn('Startup summary is not available for this app', startup.get('SummaryFetchStatus', ''))

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    @mock.patch('requests.get')
    def test_troubleshoot_status_machine_name_as_instance(
            self, requests_get_mock, send_raw_request_mock, _scm_url_mock, _headers_mock):
        """User passes a friendly machineName for --instance; we should resolve it to
        the hex ARM instanceId before calling /siteStatus."""
        arm_item = {'instanceId': '7c2d9', 'state': 'Started', 'action': 'SiteStarted'}
        send_raw_request_mock.side_effect = [
            mock.MagicMock(json=mock.MagicMock(return_value=self._instances_payload(
                {'7c2d9': 'lw0sdlwk0007AB'}))),
            mock.MagicMock(json=mock.MagicMock(return_value=self._arm_response(arm_item))),
        ]
        requests_get_mock.return_value = self._make_response(
            200, json_data=[{'InstanceId': 'lw0sdlwk0007AB',
                             'Startup': {'Succeeded': 1, 'Failed': 0}}])

        result = troubleshoot_status(self.cmd, 'myRG', 'myApp', instance='lw0sdlwk0007AB')

        # ARM /siteStatus must use the hex id even though user passed the machine name.
        arm_urls = [call.args[2] for call in send_raw_request_mock.call_args_list]
        self.assertIn('/siteStatus/7c2d9?', arm_urls[1])
        self.assertEqual(result['instances'][0]['machineName'], 'lw0sdlwk0007AB')

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    def test_troubleshoot_status_unknown_instance_raises(
            self, send_raw_request_mock, _scm_url_mock, _headers_mock):
        """User passes an --instance that matches neither hex id nor machineName."""
        send_raw_request_mock.return_value = mock.MagicMock(
            json=mock.MagicMock(return_value=self._instances_payload({'7c2d9': 'lw0sdlwk0007AB'})))

        with self.assertRaises(ResourceNotFoundError):
            troubleshoot_status(self.cmd, 'myRG', 'myApp', instance='does-not-exist')

    def test_troubleshoot_status_raises_on_windows(self):
        with mock.patch('azure.cli.command_modules.appservice.custom.is_linux_webapp',
                        return_value=False):
            with self.assertRaises(ArgumentUsageError) as cm:
                troubleshoot_status(self.cmd, 'myRG', 'myWindowsApp')
        self.assertIn('Linux', str(cm.exception))

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer token'})
    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    @mock.patch('requests.get')
    @mock.patch('azure.cli.command_modules.appservice._troubleshoot_status_report.render_report')
    def test_troubleshoot_status_report_flag_renders_and_returns_none(
            self, render_mock, requests_get_mock, send_raw_request_mock,
            _scm_url_mock, _headers_mock):
        """With --report, command calls the renderer and returns None (no structured payload)."""
        arm_item = {'instanceId': '7c2d9', 'state': 'Running'}
        send_raw_request_mock.side_effect = [
            mock.MagicMock(json=mock.MagicMock(return_value=self._instances_payload(
                {'7c2d9': 'lw0sdlwk0007AB'}))),
            mock.MagicMock(json=mock.MagicMock(return_value=self._arm_response(arm_item))),
        ]
        requests_get_mock.return_value = self._make_response(
            200, json_data=[{'InstanceId': 'lw0sdlwk0007AB',
                             'Startup': {'Succeeded': 1, 'Failed': 0}}])

        result = troubleshoot_status(self.cmd, 'myRG', 'myApp', report=True)

        self.assertIsNone(result)
        render_mock.assert_called_once()
        rendered_payload = render_mock.call_args.args[0]
        self.assertEqual(rendered_payload['name'], 'myApp')
        self.assertEqual(rendered_payload['instances'][0]['instanceId'], '7c2d9')

    def test_transform_troubleshoot_status_output_renders_error_columns(self):
        # Regression: the LastError* columns exercise _format_dt only when
        # any instance has a visible error. A missing import there surfaces
        # as knack's opaque "Table output unavailable" message.
        from azure.cli.command_modules.appservice.commands import (
            transform_troubleshoot_status_output,
        )
        payload = {
            'name': 'myApp',
            'resourceGroup': 'myRG',
            'instances': [
                {
                    'instanceId': 'b6cc022ee0e1234567890',
                    'state': 'Stopped',
                    'details': 'container did not start',
                    'lastError': 'ContainerTimeout',
                    'lastErrorTimestamp': '2026-07-13T17:29:10Z',
                    'lastErrorDetails': 'boom',
                    'startup': {'Succeeded': 1, 'Failed': 2},
                },
            ],
        }
        rows = transform_troubleshoot_status_output(payload)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['InstanceId'], 'b6cc022ee0')
        self.assertEqual(row['LastError'], 'ContainerTimeout')
        self.assertIn('2026-07-13', row['LastErrorTimestamp'])
        self.assertEqual(row['LastErrorDetails'], 'boom')
        self.assertEqual(row['Succeeded (last 24h)'], 1)
        self.assertEqual(row['Failed (last 24h)'], 2)


class TestRuntimeFailedHintMocked(unittest.TestCase):
    """Tests that the TIP hint appears in RuntimeFailed and timeout errors."""

    def _make_deployment_response(self, status, num_in_progress=0, num_successful=0,
                                  num_failed=1, errors=None, failure_logs=None):
        return {
            'properties': {
                'status': status,
                'numberOfInstancesInProgress': str(num_in_progress),
                'numberOfInstancesSuccessful': str(num_successful),
                'numberOfInstancesFailed': str(num_failed),
                'errors': errors or [],
                'failedInstancesLogs': failure_logs,
            }
        }

    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.time.sleep')
    @mock.patch('azure.cli.command_modules.appservice.custom.time.time')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    def test_runtime_failed_includes_startup_log_hint(self, send_raw_mock, time_mock,
                                                      sleep_mock, _scm_url_mock):
        from azure.cli.command_modules.appservice.custom import _poll_deployment_runtime_status

        time_mock.return_value = 10  # constant — never times out, RuntimeFailed triggers on first iteration
        resp_mock = mock.MagicMock()
        resp_mock.json.return_value = self._make_deployment_response('RuntimeFailed')
        send_raw_mock.return_value = resp_mock

        with self.assertRaises(CLIError) as cm:
            _poll_deployment_runtime_status(
                _get_test_cmd(), 'myRG', 'myApp', None,
                'https://management.azure.com/deploymentstatus', 'deploy-id-1'
            )

        error_msg = str(cm.exception)
        self.assertIn('az webapp log startup show -n myApp -g myRG', error_msg)
        self.assertIn('failed to start', error_msg)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    @mock.patch('azure.cli.command_modules.appservice.custom.time.sleep')
    @mock.patch('azure.cli.command_modules.appservice.custom.time.time')
    @mock.patch('azure.cli.command_modules.appservice.custom.send_raw_request')
    def test_timeout_includes_startup_log_hint(self, send_raw_mock, time_mock,
                                               sleep_mock, _scm_url_mock):
        from azure.cli.command_modules.appservice.custom import _poll_deployment_runtime_status
        import itertools

        # Advancing counter: each call returns 0, 1, 2, ... — exceeds timeout=1 after first loop
        time_mock.side_effect = itertools.count(0)
        resp_mock = mock.MagicMock()
        resp_mock.json.return_value = self._make_deployment_response('RuntimeStarting')
        send_raw_mock.return_value = resp_mock

        with self.assertRaises(CLIError) as cm:
            _poll_deployment_runtime_status(
                _get_test_cmd(), 'myRG', 'myApp', None,
                'https://management.azure.com/deploymentstatus', 'deploy-id-1',
                timeout=1
            )

        error_msg = str(cm.exception)
        self.assertIn('az webapp log startup show -n myApp -g myRG', error_msg)
        self.assertIn('Timeout', error_msg)


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


class TestOneDeployScmCache(unittest.TestCase):
    """Tests for the per-invocation SCM URL / SCM headers cache on OneDeployParams.

    The cache avoids duplicate `_get_scm_url` and `get_scm_site_headers` round
    trips between the publish leg and the status-poll leg of a single
    `az webapp deploy` invocation. See _perform_onedeploy_internal +
    _check_zip_deployment_status in custom.py.
    """

    def _make_params(self):
        from azure.cli.command_modules.appservice.custom import OneDeployParams
        params = OneDeployParams()
        params.cmd = mock.MagicMock()
        params.cmd.cli_ctx = mock.MagicMock()
        params.cmd.cli_ctx.data = {'headers': {'x-ms-client-request-id': 'req-1'}}
        params.resource_group_name = 'myRG'
        params.webapp_name = 'myApp'
        params.slot = None
        return params

    def test_get_or_fetch_scm_url_derives_from_cached_site(self):
        from azure.cli.command_modules.appservice.custom import _get_or_fetch_scm_url
        from azure.mgmt.web.models import HostType
        params = self._make_params()
        # Simulate a cached Site with a repository host
        repo_host = mock.MagicMock()
        repo_host.host_type = HostType.repository
        repo_host.name = 'myapp.scm.azurewebsites.net'
        std_host = mock.MagicMock()
        std_host.host_type = HostType.standard
        std_host.name = 'myapp.azurewebsites.net'
        params._cached_site = mock.MagicMock()
        params._cached_site.host_name_ssl_states = [std_host, repo_host]

        first = _get_or_fetch_scm_url(params)
        second = _get_or_fetch_scm_url(params)

        self.assertEqual(first, 'https://myapp.scm.azurewebsites.net')
        self.assertEqual(second, first)

    @mock.patch('azure.cli.command_modules.appservice.custom._get_scm_url',
                return_value='https://myapp.scm.azurewebsites.net')
    def test_get_or_fetch_scm_url_falls_back_when_no_cached_site(self, get_scm_url_mock):
        from azure.cli.command_modules.appservice.custom import _get_or_fetch_scm_url
        params = self._make_params()
        params._cached_site = None

        result = _get_or_fetch_scm_url(params)

        self.assertEqual(result, 'https://myapp.scm.azurewebsites.net')
        get_scm_url_mock.assert_called_once_with(params.cmd, 'myRG', 'myApp', None)

    def test_populate_cached_scm_headers_basic_auth_lowercase_key(self):
        # The basic-auth branch of get_scm_site_headers builds headers via
        # urllib3.util.make_headers(basic_auth=...), which uses a lowercase
        # 'authorization' key (verified with urllib3 in CI). The cache must
        # match case-insensitively so the customer's actual Windows + basic
        # auth code path is covered.
        from azure.cli.command_modules.appservice.custom import _populate_cached_scm_headers
        params = self._make_params()
        headers = {
            'authorization': 'Basic ****',
            'User-Agent': 'AzureCLI/2.86.0',
            'x-ms-client-request-id': 'req-1',
            'Content-Type': 'application/octet-stream',
            'Cache-Control': 'no-cache',
        }

        _populate_cached_scm_headers(params, headers)

        # Lowercase key preserved (byte-equivalent to a fresh fetch on this
        # path). User-Agent included. Request id and content-type excluded.
        self.assertEqual(set(params._cached_scm_headers.keys()), {'authorization', 'User-Agent'})
        self.assertEqual(params._cached_scm_headers['authorization'], 'Basic ****')

    def test_populate_cached_scm_headers_aad_capitalized_key(self):
        # The AAD branch of get_scm_site_headers sets headers["Authorization"]
        # (capitalized) for the Bearer token.
        from azure.cli.command_modules.appservice.custom import _populate_cached_scm_headers
        params = self._make_params()
        headers = {
            'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJ...',
            'User-Agent': 'AzureCLI/2.86.0',
            'x-ms-client-request-id': 'req-1',
        }

        _populate_cached_scm_headers(params, headers)

        self.assertEqual(set(params._cached_scm_headers.keys()), {'Authorization', 'User-Agent'})
        self.assertEqual(params._cached_scm_headers['Authorization'], 'Bearer eyJ0eXAiOiJKV1QiLCJ...')

    def test_populate_cached_scm_headers_noop_without_authorization(self):
        from azure.cli.command_modules.appservice.custom import _populate_cached_scm_headers
        params = self._make_params()

        _populate_cached_scm_headers(params, {'Content-Type': 'application/octet-stream'})

        self.assertIsNone(params._cached_scm_headers)

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers')
    @mock.patch('azure.cli.command_modules.appservice.custom.time.sleep')
    @mock.patch('requests.get')
    def test_check_zip_deployment_status_reuses_cached_headers(
            self, requests_get_mock, _sleep_mock, get_scm_site_headers_mock):
        from azure.cli.command_modules.appservice.custom import _check_zip_deployment_status
        params = self._make_params()
        params._cached_scm_headers = {
            'Authorization': 'Basic ****',
            'User-Agent': 'AzureCLI/test',
        }
        # If the cache is honored, get_scm_site_headers must not be called.
        get_scm_site_headers_mock.side_effect = AssertionError(
            'get_scm_site_headers must not be called when cache is populated')

        resp = mock.MagicMock()
        resp.status_code = 200
        resp.json.return_value = {'status': 4}
        requests_get_mock.return_value = resp

        result = _check_zip_deployment_status(
            params.cmd, 'myRG', 'myApp',
            'https://myapp.scm.azurewebsites.net/api/deployments/latest',
            None, timeout=10, deploy_params=params)

        self.assertEqual(result.get('status'), 4)
        # Auth + UA reused from cache; request id refreshed from cmd.
        sent_headers = requests_get_mock.call_args.kwargs['headers']
        self.assertEqual(sent_headers['Authorization'], 'Basic ****')
        self.assertEqual(sent_headers['User-Agent'], 'AzureCLI/test')
        self.assertEqual(sent_headers['x-ms-client-request-id'], 'req-1')

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers')
    @mock.patch('azure.cli.command_modules.appservice.custom.time.sleep')
    @mock.patch('requests.get')
    def test_check_zip_deployment_status_reuses_cached_headers_basic_auth(
            self, requests_get_mock, _sleep_mock, get_scm_site_headers_mock):
        # Integration-style test: feed the cache via _populate_cached_scm_headers
        # using the exact dict shape urllib3 produces on the basic-auth path
        # (lowercase 'authorization'), then verify the status poller forwards
        # the credential correctly. This is the customer's actual code path.
        from azure.cli.command_modules.appservice.custom import (
            _populate_cached_scm_headers, _check_zip_deployment_status)
        params = self._make_params()
        _populate_cached_scm_headers(params, {
            'authorization': 'Basic ****',  # lowercase from urllib3
            'User-Agent': 'AzureCLI/test',
            'x-ms-client-request-id': 'publish-leg-id',
            'Content-Type': 'application/octet-stream',
        })
        get_scm_site_headers_mock.side_effect = AssertionError(
            'get_scm_site_headers must not be called when cache is populated')

        resp = mock.MagicMock()
        resp.status_code = 200
        resp.json.return_value = {'status': 4}
        requests_get_mock.return_value = resp

        _check_zip_deployment_status(
            params.cmd, 'myRG', 'myApp',
            'https://myapp.scm.azurewebsites.net/api/deployments/latest',
            None, timeout=10, deploy_params=params)

        sent_headers = requests_get_mock.call_args.kwargs['headers']
        # Lowercase key faithfully forwarded — HTTP is case-insensitive so the
        # server treats this the same as 'Authorization'.
        self.assertEqual(sent_headers['authorization'], 'Basic ****')
        self.assertEqual(sent_headers['User-Agent'], 'AzureCLI/test')
        # Fresh request id, not the one from the publish leg.
        self.assertEqual(sent_headers['x-ms-client-request-id'], 'req-1')
        self.assertNotIn('Content-Type', sent_headers)

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Bearer fresh', 'User-Agent': 'AzureCLI/test'})
    @mock.patch('azure.cli.command_modules.appservice.custom.time.sleep')
    @mock.patch('requests.get')
    def test_check_zip_deployment_status_falls_back_when_no_cache(
            self, requests_get_mock, _sleep_mock, get_scm_site_headers_mock):
        from azure.cli.command_modules.appservice.custom import _check_zip_deployment_status

        resp = mock.MagicMock()
        resp.status_code = 200
        resp.json.return_value = {'status': 4}
        requests_get_mock.return_value = resp

        # No deploy_params at all — legacy enable_zip_deploy call shape.
        cmd = mock.MagicMock()
        cmd.cli_ctx = mock.MagicMock()
        _check_zip_deployment_status(
            cmd, 'myRG', 'myApp',
            'https://myapp.scm.azurewebsites.net/api/deployments/latest',
            None, timeout=10)

        get_scm_site_headers_mock.assert_called_once_with(cmd.cli_ctx, 'myApp', 'myRG', None)

    @mock.patch('azure.cli.command_modules.appservice.custom.get_scm_site_headers',
                return_value={'Authorization': 'Basic ****', 'User-Agent': 'AzureCLI/test'})
    @mock.patch('azure.cli.command_modules.appservice.custom.time.sleep')
    @mock.patch('requests.get')
    def test_check_zip_deployment_status_refreshes_on_401(
            self, requests_get_mock, _sleep_mock, get_scm_site_headers_mock):
        from azure.cli.command_modules.appservice.custom import _check_zip_deployment_status
        params = self._make_params()
        params._cached_scm_headers = {
            'Authorization': 'Basic ****',
            'User-Agent': 'AzureCLI/test',
        }

        resp_401 = mock.MagicMock()
        resp_401.status_code = 401
        resp_ok = mock.MagicMock()
        resp_ok.status_code = 200
        resp_ok.json.return_value = {'status': 4}
        requests_get_mock.side_effect = [resp_401, resp_ok]

        result = _check_zip_deployment_status(
            params.cmd, 'myRG', 'myApp',
            'https://myapp.scm.azurewebsites.net/api/deployments/latest',
            None, timeout=10, deploy_params=params)

        self.assertEqual(result.get('status'), 4)
        # After 401 we refetched once and replaced the cached headers. The
        # is_flex_hint defaults to None when params.is_functionapp is None
        # (test setup); the refresh respects whatever the hint helper returns.
        get_scm_site_headers_mock.assert_called_once_with(
            params.cmd.cli_ctx, 'myApp', 'myRG', None, is_flex_hint=None)
        self.assertEqual(params._cached_scm_headers['Authorization'], 'Basic ****')
        # Second request used the fresh credentials.
        second_call_headers = requests_get_mock.call_args_list[1].kwargs['headers']
        self.assertEqual(second_call_headers['Authorization'], 'Basic ****')

    @mock.patch('azure.cli.command_modules.appservice.custom._make_onedeploy_request')
    @mock.patch('azure.cli.command_modules.appservice.custom._update_artifact_type')
    def test_perform_onedeploy_internal_clears_cache_on_success(
            self, _update_type_mock, make_request_mock):
        from azure.cli.command_modules.appservice.custom import _perform_onedeploy_internal
        params = self._make_params()
        params.enriched_errors = False
        params.is_linux_webapp = False
        params.is_functionapp = False

        def _populate_and_succeed(_params):
            _params._cached_scm_headers = {'Authorization': 'Basic ****'}
            _params._cached_site = mock.MagicMock(name='site')
            return {'status': 'ok'}
        make_request_mock.side_effect = _populate_and_succeed

        result = _perform_onedeploy_internal(params)

        self.assertEqual(result, {'status': 'ok'})
        # finally block must drop all caches even on the happy path.
        self.assertIsNone(params._cached_scm_headers)
        self.assertIsNone(params._cached_site)

    @mock.patch('azure.cli.command_modules.appservice.custom._make_onedeploy_request')
    @mock.patch('azure.cli.command_modules.appservice.custom._update_artifact_type')
    def test_perform_onedeploy_internal_clears_cache_on_exception(
            self, _update_type_mock, make_request_mock):
        from azure.cli.command_modules.appservice.custom import _perform_onedeploy_internal
        params = self._make_params()
        params.enriched_errors = False
        params.is_linux_webapp = False
        params.is_functionapp = False

        def _populate_and_raise(_params):
            _params._cached_scm_headers = {'Authorization': 'Basic ****'}
            _params._cached_site = mock.MagicMock(name='site')
            raise RuntimeError('boom')
        make_request_mock.side_effect = _populate_and_raise

        with self.assertRaises(RuntimeError):
            _perform_onedeploy_internal(params)

        # finally block must drop all caches before the exception propagates,
        # so telemetry / outer handlers cannot see the credential.
        self.assertIsNone(params._cached_scm_headers)
        self.assertIsNone(params._cached_site)

    def test_one_deploy_params_repr_does_not_leak_credentials(self):
        from azure.cli.command_modules.appservice.custom import OneDeployParams
        params = OneDeployParams()
        params._cached_scm_headers = {'Authorization': 'Basic ****'}
        # The default repr is the object id; it must not contain attribute
        # values. If a future change adds a __repr__/__str__ that serializes
        # the cache, this test fails so the reviewer is forced to think about
        # the credential exposure.
        self.assertNotIn('Basic', repr(params))
        self.assertNotIn('c2VjcmV0', repr(params))
        self.assertNotIn('Basic', str(params))

    def test_known_is_flex_hint_web_app(self):
        # Web apps (is_functionapp=False) can never be FlexConsumption, so the
        # hint short-circuits the is_flex_functionapp ARM call.
        from azure.cli.command_modules.appservice.custom import _known_is_flex_hint
        params = self._make_params()
        params.is_functionapp = False
        self.assertEqual(_known_is_flex_hint(params), False)

    def test_known_is_flex_hint_function_app(self):
        # When the cached site has a sku, derive the answer directly.
        from azure.cli.command_modules.appservice.custom import _known_is_flex_hint
        params = self._make_params()
        params.is_functionapp = True
        # No cached site → cannot determine, return None
        params._cached_site = None
        self.assertIsNone(_known_is_flex_hint(params))
        # Cached site with FlexConsumption SKU → True
        params._cached_site = mock.MagicMock(sku='FlexConsumption')
        self.assertTrue(_known_is_flex_hint(params))
        # Cached site with different SKU → False
        params._cached_site = mock.MagicMock(sku='Dynamic')
        self.assertFalse(_known_is_flex_hint(params))

    def test_known_is_flex_hint_unknown(self):
        # Defensive: if is_functionapp hasn't been populated and no cached site,
        # don't pretend to know.
        from azure.cli.command_modules.appservice.custom import _known_is_flex_hint
        params = self._make_params()
        params.is_functionapp = None
        params._cached_site = None
        self.assertIsNone(_known_is_flex_hint(params))
        self.assertIsNone(_known_is_flex_hint(None))

    @mock.patch('azure.cli.command_modules.appservice.custom.is_flex_functionapp')
    @mock.patch('azure.cli.command_modules.appservice.custom.basic_auth_supported', return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._get_site_credential',
                return_value=('user', 'pass'))
    @mock.patch('azure.cli.command_modules.appservice.custom.get_az_user_agent', return_value='AzureCLI/test')
    def test_get_scm_site_headers_skips_is_flex_when_hint_provided(
            self, _ua_mock, _cred_mock, _basic_auth_mock, is_flex_mock):
        # When the caller passes is_flex_hint=False, is_flex_functionapp must
        # not be invoked — saves one ARM call (GET /sites api 2023-12-01).
        from azure.cli.command_modules.appservice.custom import get_scm_site_headers
        cli_ctx = mock.MagicMock()
        cli_ctx.data = {'headers': {'x-ms-client-request-id': 'req-1'}}
        is_flex_mock.side_effect = AssertionError(
            'is_flex_functionapp must not be called when is_flex_hint is provided')

        headers = get_scm_site_headers(cli_ctx, 'myApp', 'myRG', None, is_flex_hint=False)

        # Basic-auth branch was selected because is_flex=False (from hint).
        is_flex_mock.assert_not_called()
        self.assertIn('authorization', headers)  # lowercase from urllib3
        self.assertTrue(headers['authorization'].startswith('Basic '))

    @mock.patch('azure.cli.command_modules.appservice.custom.is_flex_functionapp', return_value=False)
    @mock.patch('azure.cli.command_modules.appservice.custom.basic_auth_supported', return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._get_site_credential',
                return_value=('user', 'pass'))
    @mock.patch('azure.cli.command_modules.appservice.custom.get_az_user_agent', return_value='AzureCLI/test')
    def test_get_scm_site_headers_calls_is_flex_when_no_hint(
            self, _ua_mock, _cred_mock, _basic_auth_mock, is_flex_mock):
        # Backward-compat: when no hint is provided (existing callers),
        # is_flex_functionapp is invoked exactly as before.
        from azure.cli.command_modules.appservice.custom import get_scm_site_headers
        cli_ctx = mock.MagicMock()
        cli_ctx.data = {'headers': {'x-ms-client-request-id': 'req-1'}}

        get_scm_site_headers(cli_ctx, 'myApp', 'myRG', None)

        is_flex_mock.assert_called_once_with(cli_ctx, 'myRG', 'myApp')


class TestOneDeploySiteCache(unittest.TestCase):
    """Tests for the per-invocation Site cache on OneDeployParams.

    The Site cache dedupes GET /sites calls between perform_onedeploy_webapp,
    _get_onedeploy_request_body (is_linux check),
    _check_runtimestatus_with_deploymentstatusapi (is_linux check), and the
    success-log URL builder. See _get_or_fetch_site / _get_or_fetch_is_linux_webapp
    / _get_visit_url / _url_from_site in custom.py.
    """

    def _make_params(self):
        from azure.cli.command_modules.appservice.custom import OneDeployParams
        params = OneDeployParams()
        params.cmd = mock.MagicMock()
        params.cmd.cli_ctx = mock.MagicMock()
        params.resource_group_name = 'myRG'
        params.webapp_name = 'myApp'
        params.slot = None
        return params

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_get_or_fetch_site_caches_result(self, generic_op_mock):
        from azure.cli.command_modules.appservice.custom import _get_or_fetch_site
        params = self._make_params()
        sentinel_site = mock.MagicMock(name='site')
        generic_op_mock.return_value = sentinel_site

        first = _get_or_fetch_site(params)
        second = _get_or_fetch_site(params)
        third = _get_or_fetch_site(params)

        self.assertIs(first, sentinel_site)
        self.assertIs(second, sentinel_site)
        self.assertIs(third, sentinel_site)
        generic_op_mock.assert_called_once_with(
            params.cmd.cli_ctx, 'myRG', 'myApp', 'get', None)

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_get_or_fetch_site_uses_slot_when_set(self, generic_op_mock):
        # When params.slot is set, the cached Site must be the slot's Site
        # (via get_slot under the hood), not the production Site. Slots have
        # their own host_name_ssl_states and enabled_host_names, so
        # _get_visit_url would otherwise show the wrong URL.
        from azure.cli.command_modules.appservice.custom import _get_or_fetch_site
        params = self._make_params()
        params.slot = 'staging'
        slot_site = mock.MagicMock(name='slotSite')
        generic_op_mock.return_value = slot_site

        result = _get_or_fetch_site(params)

        self.assertIs(result, slot_site)
        generic_op_mock.assert_called_once_with(
            params.cmd.cli_ctx, 'myRG', 'myApp', 'get', 'staging')

    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_get_or_fetch_is_linux_webapp_uses_cached_value(self, generic_op_mock):
        # perform_onedeploy_webapp populates is_linux_webapp eagerly; the
        # helper must not re-fetch when the answer is already known.
        from azure.cli.command_modules.appservice.custom import _get_or_fetch_is_linux_webapp
        params = self._make_params()
        params.is_linux_webapp = True

        self.assertTrue(_get_or_fetch_is_linux_webapp(params))
        generic_op_mock.assert_not_called()

        params.is_linux_webapp = False
        self.assertFalse(_get_or_fetch_is_linux_webapp(params))
        generic_op_mock.assert_not_called()

    @mock.patch('azure.cli.command_modules.appservice.custom.is_linux_webapp', return_value=True)
    @mock.patch('azure.cli.command_modules.appservice.custom._generic_site_operation')
    def test_get_or_fetch_is_linux_webapp_lazy_fetch_for_functionapp(
            self, generic_op_mock, is_linux_mock):
        # perform_onedeploy_functionapp does NOT pre-populate is_linux_webapp,
        # so the first consumer must lazily fetch + cache the Site.
        from azure.cli.command_modules.appservice.custom import _get_or_fetch_is_linux_webapp
        params = self._make_params()
        params.is_linux_webapp = None
        site = mock.MagicMock(name='site')
        generic_op_mock.return_value = site

        first = _get_or_fetch_is_linux_webapp(params)
        second = _get_or_fetch_is_linux_webapp(params)

        self.assertTrue(first)
        self.assertTrue(second)
        # Site fetched exactly once even across multiple lookups.
        generic_op_mock.assert_called_once()
        is_linux_mock.assert_called_once_with(site)
        # Result is memoized on params for subsequent helpers (e.g. the
        # status poller).
        self.assertTrue(params.is_linux_webapp)
        self.assertIs(params._cached_site, site)

    def test_url_from_site_picks_https_when_ssl_enabled(self):
        from azure.cli.command_modules.appservice.custom import _url_from_site
        SslState = mock.MagicMock()
        SslState.disabled = 'Disabled'
        cmd = mock.MagicMock()
        cmd.get_models.return_value = SslState
        site = mock.MagicMock()
        site.enabled_host_names = ['custom.contoso.com', 'myapp.azurewebsites.net']
        site.host_name_ssl_states = [
            mock.MagicMock(ssl_state='SniEnabled'),
        ]

        self.assertEqual(
            _url_from_site(cmd, site), 'https://custom.contoso.com')

    def test_url_from_site_picks_http_when_no_ssl(self):
        from azure.cli.command_modules.appservice.custom import _url_from_site
        SslState = mock.MagicMock()
        SslState.disabled = 'Disabled'
        cmd = mock.MagicMock()
        cmd.get_models.return_value = SslState
        site = mock.MagicMock()
        site.enabled_host_names = ['myapp.azurewebsites.net']
        site.host_name_ssl_states = [
            mock.MagicMock(ssl_state='Disabled'),
            mock.MagicMock(ssl_state='Disabled'),
        ]

        self.assertEqual(
            _url_from_site(cmd, site), 'http://myapp.azurewebsites.net')

    @mock.patch('azure.cli.command_modules.appservice.custom._get_url')
    @mock.patch('azure.cli.command_modules.appservice.custom._url_from_site',
                return_value='https://myapp.azurewebsites.net')
    def test_get_visit_url_uses_cached_site(self, url_from_site_mock, get_url_mock):
        # When the Site is already cached (the common case after
        # perform_onedeploy_webapp), no fallback ARM call should be made.
        from azure.cli.command_modules.appservice.custom import _get_visit_url
        params = self._make_params()
        params._cached_site = mock.MagicMock(name='site')

        result = _get_visit_url(params)

        self.assertEqual(result, 'https://myapp.azurewebsites.net')
        url_from_site_mock.assert_called_once_with(params.cmd, params._cached_site)
        get_url_mock.assert_not_called()

    @mock.patch('azure.cli.command_modules.appservice.custom._get_url')
    @mock.patch('azure.cli.command_modules.appservice.custom._url_from_site',
                return_value='https://myapp-staging.azurewebsites.net')
    def test_get_visit_url_uses_cached_slot_site(self, url_from_site_mock, get_url_mock):
        # For slot deployments, perform_onedeploy_webapp fetches the slot's
        # Site, so _get_visit_url can still serve the URL from the cache.
        from azure.cli.command_modules.appservice.custom import _get_visit_url
        params = self._make_params()
        params.slot = 'staging'
        params._cached_site = mock.MagicMock(name='slotSite')

        result = _get_visit_url(params)

        self.assertEqual(result, 'https://myapp-staging.azurewebsites.net')
        url_from_site_mock.assert_called_once_with(params.cmd, params._cached_site)
        get_url_mock.assert_not_called()

    @mock.patch('azure.cli.command_modules.appservice.custom._get_url',
                return_value='https://myapp.azurewebsites.net')
    def test_get_visit_url_falls_back_when_no_cache(self, get_url_mock):
        # perform_onedeploy_functionapp does not populate _cached_site; in
        # that path we must still produce a URL via the standard helper.
        from azure.cli.command_modules.appservice.custom import _get_visit_url
        params = self._make_params()
        params._cached_site = None
        params.slot = None

        result = _get_visit_url(params)

        self.assertEqual(result, 'https://myapp.azurewebsites.net')
        get_url_mock.assert_called_once_with(params.cmd, 'myRG', 'myApp', None)


class _TypespecContainerSettings(Mapping):
    """Mimics an azure-mgmt-web typespec/DPG container settings model.

    The current SDK returns models that behave like a read-only ``Mapping`` keyed
    by the raw camelCase API field names (e.g. ``runtimes``, ``isAutoUpdate``,
    ``java25Runtime``). They also expose the few fields the SDK explicitly models
    as snake_case attributes (``java8_runtime``/``java11_runtime``). Crucially,
    unknown fields are NOT surfaced via the old msrest ``additional_properties``
    dict -- that attribute stays empty. The list-runtimes regression came from
    reading only the typed attributes / ``additional_properties`` (which together
    cover at most Java 8/11) instead of the Mapping data, silently dropping
    Java 17/21/25.
    """

    def __init__(self, data, *, java8=None, java11=None, is_auto_update=False,
                 end_of_life_date=None):
        self._data = dict(data)
        self.java8_runtime = java8
        self.java11_runtime = java11
        self.is_auto_update = is_auto_update
        self.end_of_life_date = end_of_life_date
        self.is_hidden = False
        self.is_deprecated = False
        # Typespec models leave additional_properties empty (msrest-only concept).
        self.additional_properties = []

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class TestStackRuntimeJavaSELinux(unittest.TestCase):
    """Regression tests for `az webapp list-runtimes` Linux Java SE parsing.

    The displayed Linux Java SE runtimes come from a single aggregate auto-update
    container whose ``runtimes`` array enumerates every available Java major
    version (8/11/17/21/25). The azure-mgmt-web SDK now returns typespec models
    that preserve those fields via the Mapping interface rather than the typed
    java8/java11 attributes or msrest ``additional_properties``. These tests guard
    against the regression where newer Java versions were dropped because only the
    typed attributes / ``additional_properties`` were consulted, and against the
    aggregate container's position in the response mattering.
    """

    EXPECTED = {
        'JAVA|25-java25', 'JAVA|21-java21', 'JAVA|17-java17', 'JAVA|11-java11', 'JAVA|8-jre8',
    }

    FULL_RUNTIMES = [
        {'runtimeVersion': '8', 'runtime': 'JAVA|8-jre8'},
        {'runtimeVersion': '11', 'runtime': 'JAVA|11-java11'},
        {'runtimeVersion': '17', 'runtime': 'JAVA|17-java17'},
        {'runtimeVersion': '21', 'runtime': 'JAVA|21-java21'},
        {'runtimeVersion': '25', 'runtime': 'JAVA|25-java25'},
    ]

    @staticmethod
    def _minor(value, container_settings):
        stack_settings = types.SimpleNamespace(
            linux_container_settings=container_settings,
            linux_runtime_settings=None,
            windows_container_settings=None,
            windows_runtime_settings=None,
        )
        return types.SimpleNamespace(value=value, stack_settings=stack_settings)

    def _patch_minors(self):
        # Per-patch Java SE minors are always present in the API response, one per
        # build. They are NOT auto-update and must never drive the displayed output.
        return [
            self._minor('25.0.1', _TypespecContainerSettings(
                {'runtimes': [{'runtimeVersion': '25', 'runtime': 'JAVA|25.0.1'}]})),
            self._minor('21.0.9', _TypespecContainerSettings(
                {'runtimes': [{'runtimeVersion': '21', 'runtime': 'JAVA|21.0.9'}]})),
            self._minor('17.0.17', _TypespecContainerSettings(
                {'runtimes': [{'runtimeVersion': '17', 'runtime': 'JAVA|17.0.17'}]})),
            self._minor('11.0.29', _TypespecContainerSettings(
                {'runtimes': [{'runtimeVersion': '11', 'runtime': 'JAVA|11.0.29'}]})),
            self._minor('1.8.472', _TypespecContainerSettings(
                {'runtimes': [{'runtimeVersion': '8', 'runtime': 'JAVA|1.8.472'}]})),
        ]

    @staticmethod
    def _java_se_stack(minors):
        major = types.SimpleNamespace(
            display_text='Java SE (Embedded Web Server)',
            minor_versions=minors,
        )
        return types.SimpleNamespace(display_text='Java Containers', major_versions=[major])

    @staticmethod
    def _new_helper():
        from azure.cli.command_modules.appservice.custom import _StackRuntimeHelper
        helper = _StackRuntimeHelper.__new__(_StackRuntimeHelper)
        helper._linux = True
        helper._windows = False
        helper._include_eol = False
        helper._stacks = []
        helper.windows_config_mappings = {'node': None}
        return helper

    def _java_se_configs(self, stack):
        helper = self._new_helper()
        helper._parse_raw_stacks([stack])
        rows = helper.get_stacks_as_table(runtime_filter='java', support_filter=None)
        return {r['config'] for r in rows if r['runtime'] == 'Java'}

    def test_aggregate_runtimes_array_complete(self):
        # Primary path: the aggregate auto-update container carries the full
        # 'runtimes' array via the typespec Mapping interface.
        aggregate = self._minor('SE', _TypespecContainerSettings(
            {'isAutoUpdate': True, 'runtimes': self.FULL_RUNTIMES}, is_auto_update=True))
        stack = self._java_se_stack([aggregate] + self._patch_minors())
        self.assertEqual(self._java_se_configs(stack), self.EXPECTED)

    def test_aggregate_javaNNRuntime_keys(self):
        # Fallback path: no 'runtimes' array, but the Mapping exposes individual
        # javaNNRuntime camelCase keys for every available major version.
        aggregate = self._minor('SE', _TypespecContainerSettings(
            {
                'isAutoUpdate': True,
                'java8Runtime': 'JAVA|8-jre8',
                'java11Runtime': 'JAVA|11-java11',
                'java17Runtime': 'JAVA|17-java17',
                'java21Runtime': 'JAVA|21-java21',
                'java25Runtime': 'JAVA|25-java25',
            },
            is_auto_update=True))
        stack = self._java_se_stack([aggregate] + self._patch_minors())
        self.assertEqual(self._java_se_configs(stack), self.EXPECTED)

    def test_aggregate_not_first_selected_by_auto_update(self):
        # The aggregate auto-update container must be chosen by its is_auto_update
        # flag, not its position -- here it is returned last, after the per-patch minors.
        aggregate = self._minor('SE', _TypespecContainerSettings(
            {'isAutoUpdate': True, 'runtimes': self.FULL_RUNTIMES}, is_auto_update=True))
        stack = self._java_se_stack(self._patch_minors() + [aggregate])
        self.assertEqual(self._java_se_configs(stack), self.EXPECTED)

    def test_typed_attrs_only_expose_java_8_11_but_mapping_has_all(self):
        # Reproduces the exact regression: the SDK types only java8_runtime /
        # java11_runtime, and additional_properties is empty, but the full data is
        # available through the Mapping. The fix must read the Mapping, not just the
        # typed attributes, otherwise Java 17/21/25 are silently dropped.
        aggregate = self._minor('SE', _TypespecContainerSettings(
            {'isAutoUpdate': True, 'runtimes': self.FULL_RUNTIMES},
            java8='JAVA|8-jre8', java11='JAVA|11-java11', is_auto_update=True))
        # Sanity-check the model: typed attrs cover only 8/11, additional_properties empty.
        self.assertEqual(aggregate.stack_settings.linux_container_settings.additional_properties, [])
        stack = self._java_se_stack([aggregate] + self._patch_minors())
        self.assertEqual(self._java_se_configs(stack), self.EXPECTED)

    def test_runtimes_array_entries_flagged_auto_update(self):
        # Entries derived from the aggregate must be flagged auto-update so they
        # survive the table filter that drops non-auto-update java rows.
        aggregate = self._minor('SE', _TypespecContainerSettings(
            {'isAutoUpdate': True, 'runtimes': self.FULL_RUNTIMES}, is_auto_update=True))
        stack = self._java_se_stack([aggregate] + self._patch_minors())
        helper = self._new_helper()
        helper._parse_raw_stacks([stack])
        java_runtimes = [s for s in helper._stacks if s.display_name in self.EXPECTED]
        self.assertEqual({s.display_name for s in java_runtimes}, self.EXPECTED)
        self.assertTrue(all(s.is_auto_update for s in java_runtimes))

    def test_get_container_settings_data_reads_mapping(self):
        from azure.cli.command_modules.appservice.custom import _StackRuntimeHelper
        settings = _TypespecContainerSettings(
            {'isAutoUpdate': True, 'java25Runtime': 'JAVA|25-java25', 'runtimes': self.FULL_RUNTIMES},
            java8='JAVA|8-jre8', java11='JAVA|11-java11', is_auto_update=True)
        data = _StackRuntimeHelper._get_container_settings_data(settings)
        self.assertTrue(data.get('isAutoUpdate'))
        self.assertEqual(data.get('java25Runtime'), 'JAVA|25-java25')
        self.assertEqual(len(data.get('runtimes')), 5)

    def test_get_java_runtimes_from_container_settings_reads_mapping(self):
        from azure.cli.command_modules.appservice.custom import _StackRuntimeHelper
        settings = _TypespecContainerSettings(
            {'isAutoUpdate': True, 'runtimes': self.FULL_RUNTIMES},
            java8='JAVA|8-jre8', java11='JAVA|11-java11', is_auto_update=True)
        runtimes = _StackRuntimeHelper._get_java_runtimes_from_container_settings(settings)
        self.assertEqual({name for name, _, _ in runtimes}, self.EXPECTED)
        self.assertTrue(all(is_auto for _, _, is_auto in runtimes))


if __name__ == '__main__':
    unittest.main()