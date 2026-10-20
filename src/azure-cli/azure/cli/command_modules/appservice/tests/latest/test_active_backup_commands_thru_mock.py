# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from contextlib import redirect_stderr, redirect_stdout
import inspect
import io
import json
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from azure.cli.core.azclierror import AzureResponseError, InvalidArgumentValueError, ResourceNotFoundError
from azure.cli.command_modules.appservice import active_backup as commands
from azure.cli.command_modules.appservice._active_backup_client import ActiveBackupClient, API_VERSION
from azure.cli.command_modules.appservice._active_backup_commands import COMMAND_GROUPS
from .test_active_backup_client import cli_context, response


MODULE = 'azure.cli.command_modules.appservice.active_backup'

# Independent route expectations from SitesCsmSurface, including each hidden API and input variant.
PASS_THROUGH_CASES = (
    ('P01', 'show_silo_php_logging', 'GET', '/phplogging', {}),
    ('P02', 'list_silo_deployments', 'GET', '/deployments', {}),
    ('P03', 'show_silo_deployment', 'GET', '/deployments/deploy', {'deployment_id': 'deploy'}),
    ('P04', 'list_silo_deployment_logs', 'GET', '/deployments/deploy/log', {'deployment_id': 'deploy'}),
    ('P05', 'delete_silo_process', 'DELETE', '/processes/123', {'process_id': '123'}),
    ('P06', 'stop_silo_process', 'POST', '/processes/123/stop', {'process_id': '123'}),
    ('P07', 'restart_silo_container', 'POST', '/containers/main/restart', {'container_name': 'main'}),
    ('P08', 'show_silo_process', 'GET', '/processes/123', {'process_id': '123'}),
    ('P09', 'list_silo_process_threads', 'GET', '/processes/123/threads', {'process_id': '123'}),
    ('P10', 'show_silo_process_thread', 'GET', '/processes/123/threads/thread',
     {'process_id': '123', 'thread_id': 'thread'}),
    ('P11', 'list_silo_process_modules', 'GET', '/processes/123/modules', {'process_id': '123'}),
    ('P12', 'show_silo_process_module', 'GET', '/processes/123/modules/0x1',
     {'process_id': '123', 'base_address': '0x1'}),
    ('P13', 'dump_silo_process', 'GET', '/processes/123/dump', {'process_id': '123', 'file': 'out.bin'}),
    ('P14', 'download_silo_container_logs', 'POST', '/containerlogs', {'format': 'raw', 'file': 'out.bin'}),
    ('P15', 'download_silo_container_logs', 'POST', '/containerlogs/zip', {'format': 'zip', 'file': 'out.bin'}),
    ('P16', 'list_silo_startup_logs', 'GET', '/startuplogs', {}),
    ('P17', 'show_silo_startup_summary', 'GET', '/startuplogs/summary', {}),
    ('P18', 'show_silo_startup_log', 'GET', '/startuplogs/startup.log', {'filename': 'startup.log'}),
    ('P19', 'list_silo_logs', 'GET', '/logs', {}),
    ('P20', 'tail_silo_logs', 'GET', '/logs/live', {}),
    ('P21', 'list_silo_webjobs', 'GET', '/webjobs', {}),
    ('P22', 'show_silo_webjob', 'GET', '/webjobs/job', {'webjob_name': 'job'}),
    ('P23', 'list_silo_continuous_webjobs', 'GET', '/continuouswebjobs', {}),
    ('P24', 'show_silo_continuous_webjob', 'GET', '/continuouswebjobs/job', {'webjob_name': 'job'}),
    ('P25', 'start_silo_continuous_webjob', 'POST', '/continuouswebjobs/job/start', {'webjob_name': 'job'}),
    ('P26', 'stop_silo_continuous_webjob', 'POST', '/continuouswebjobs/job/stop', {'webjob_name': 'job'}),
    ('P27', 'list_silo_triggered_webjobs', 'GET', '/triggeredwebjobs', {}),
    ('P28', 'show_silo_triggered_webjob', 'GET', '/triggeredwebjobs/job', {'webjob_name': 'job'}),
    ('P29', 'list_silo_webjob_history', 'GET', '/triggeredwebjobs/job/history', {'webjob_name': 'job'}),
    ('P30', 'show_silo_webjob_history', 'GET', '/triggeredwebjobs/job/history/run',
     {'webjob_name': 'job', 'run_id': 'run'}),
    ('P31', 'run_silo_triggered_webjob', 'POST', '/triggeredwebjobs/job/run', {'webjob_name': 'job'}),
    ('P32', 'list_silo_site_extensions', 'GET', '/siteextensions', {}),
    ('P33', 'show_silo_site_extension', 'GET', '/siteextensions/ext', {'extension_name': 'ext'}),
    ('P34', 'check_silo_connectivity', 'POST', '/connectivityCheck', {'body': '{"properties":{}}'}),
    ('P35', 'check_silo_dns', 'POST', '/dnsCheck', {'body': '{"properties":{}}'}),
    ('P36', 'check_silo_tcp', 'POST', '/tcpPingCheck', {'body': '{"properties":{}}'}),
    ('P37', 'invoke_silo_extension', 'GET', '/instances/worker/extensions/api/settings',
     {'instance': 'worker', 'path': 'api/settings'}),
    ('P38', 'show_silo_onedeploy_status', 'GET', '/extensions/onedeploy', {}),
    ('P39', 'show_silo_msdeploy_log', 'GET', '/extensions/MSDeploy/log', {}),
    ('P40', 'list_silo_instances', 'GET', '/instances', {}),
    ('P41', 'show_silo_instance', 'GET', '/instances/worker', {'instance': 'worker'}),
    ('P42', 'show_silo_config', 'GET', '/config/web', {}),
    ('P43', 'list_silo_config', 'GET', '/config', {}),
    ('P44', 'list_silo_config_snapshots', 'GET', '/config/web/snapshots', {}),
    ('P45', 'show_silo_config_snapshot', 'GET', '/config/web/snapshots/snap', {'snapshot_id': 'snap'}),
    ('P46', 'show_silo_config_snapshot', 'POST', '/config/web/snapshots/snap/listsecrets',
     {'snapshot_id': 'snap', 'include_secrets': True}),
    ('P47', 'list_silo_keyvault_references', 'GET', '/config/configreferences/connectionstrings', {}),
    ('P48', 'refresh_silo_keyvault_references', 'POST', '/config/configreferences/appsettings/refresh', {}),
    ('P49', 'list_silo_detected_stacks', 'GET', '/detectedstacks', {}),
    ('P50', 'list_silo_appsettings', 'POST', '/config/appsettings/list', {}),
    ('P51', 'list_silo_storage_accounts', 'POST', '/config/azurestorageaccounts/list', {}),
    ('P52', 'show_silo_connection_strings', 'GET', '/config/connectionstrings', {}),
    ('P53', 'list_silo_connection_strings', 'POST', '/config/connectionstrings/list', {}),
    ('P54', 'show_silo_connection_strings', 'POST', '/config/web/connectionstrings/key', {'key': 'key'}),
    ('P55', 'show_silo_auth', 'GET', '/config/authsettings', {'metadata_only': True}),
    ('P56', 'show_silo_auth', 'POST', '/config/authsettings/list', {}),
    ('P57', 'show_silo_auth_v2', 'GET', '/config/authsettingsV2/list', {'legacy': True}),
    ('P58', 'show_silo_auth_v2', 'GET', '/config/authsettingsV2', {}),
    ('P59', 'show_silo_push_settings', 'POST', '/config/pushsettings/list', {}),
    ('P60', 'list_silo_metadata', 'POST', '/config/metadata/list', {}),
    ('P61', 'show_silo_log_config', 'GET', '/config/logs', {}),
    ('P62', 'list_silo_premier_addons', 'GET', '/premieraddons', {}),
    ('P63', 'show_silo_premier_addon', 'GET', '/premieraddons/addon', {'addon_name': 'addon'}),
    ('P64', 'list_silo_metrics', 'GET', '/metrics', {}),
    ('P65', 'list_silo_metric_definitions', 'GET', '/metricdefinitions', {}),
    ('P66', 'list_silo_perf_counters', 'GET', '/perfcounters', {}),
    ('P67', 'restart_site_silo', 'POST', '/restart', {}),
    ('P68', 'start_site_silo', 'POST', '/start', {}),
    ('P69', 'stop_site_silo', 'POST', '/stop', {}),
    ('P70', 'start_silo_network_trace', 'POST', '/networkTrace/start', {'legacy': True}),
    ('P71', 'start_silo_network_trace', 'POST', '/networkTrace/startOperation', {}),
    ('P72', 'stop_silo_network_trace', 'POST', '/networkTrace/stop', {}),
    ('P73', 'show_silo_network_trace_operation', 'GET', '/networkTrace/operationresults/op', {'operation_id': 'op'}),
    ('P74', 'show_silo_network_trace', 'GET', '/networkTrace/op', {'operation_id': 'op'}),
    ('P75', 'show_silo_runtime_operation', 'GET', '/operations/op', {'operation_id': 'op'}),
    ('P76', 'scan_silo_antivirus', 'POST', '/antivirus/queue', {}),
    ('P77', 'show_silo_antivirus_config', 'GET', '/antivirus/config', {}),
    ('P78', 'update_silo_antivirus_config', 'PUT', '/antivirus/config', {'body': '{"properties":{}}'}),
    ('P79', 'list_silo_antivirus_logs', 'GET', '/antiviruslogs', {}),
    ('P80', 'show_silo_antivirus_log', 'POST', '/antiviruslogs/scan/list',
     {'scan_id': 'scan', 'include_file_paths': True}),
    ('P81', 'show_silo_antivirus_log', 'GET', '/antiviruslogs/scan', {'scan_id': 'scan'}),
    ('P82', 'list_silo_deployment_statuses', 'GET', '/deploymentStatus', {}),
    ('P83', 'list_silo_sitecontainers', 'GET', '/sitecontainers', {}),
    ('P84', 'show_silo_sitecontainer', 'GET', '/sitecontainers/main', {'container_name': 'main'}),
)

RESOURCE_CASES = (
    ('C01', 'list_plan_silos', True, 'GET', '/silos', {}),
    ('C02', 'show_plan_silo', True, 'GET', '/silos/backup', {'silo': 'backup'}),
    ('C03', 'create_plan_silo', True, 'PUT', '/silos/backup',
     {'silo': 'backup', 'location': 'westus2', 'primary_location': 'eastus'}),
    ('C04', 'update_plan_silo', True, 'PUT', '/silos/backup', {'silo': 'backup', 'number_of_workers': 2}),
    ('C05', 'delete_plan_silo', True, 'DELETE', '/silos/backup', {'silo': 'backup'}),
    ('C06', 'show_plan_silo_operation', True, 'GET', '/silos/backup/operationresults/op',
     {'silo': 'backup', 'operation_id': 'op'}),
    ('C07', 'list_plan_silo_vnet_integrations', True, 'GET', '/silos/backup/virtualNetworkIntegrations',
     {'silo': 'backup'}),
    ('C08', 'list_site_silos', False, 'GET', '/silos', {}),
    ('C09', 'show_site_silo', False, 'GET', '/silos/backup', {'silo': 'backup'}),
    ('C10', 'create_site_silo', False, 'PUT', '/silos/backup',
     {'silo': 'backup', 'location': 'westus2', 'primary_location': 'eastus', 'traffic_mode': 'Active'}),
    ('C11', 'update_site_silo', False, 'PUT', '/silos/backup',
     {'silo': 'backup', 'endpoint_status': 'Disabled'}),
    ('C12', 'delete_site_silo', False, 'DELETE', '/silos/backup', {'silo': 'backup'}),
    ('C13', 'show_site_silo_operation', False, 'GET', '/silos/backup/operationresults/op',
     {'silo': 'backup', 'operation_id': 'op'}),
    ('C14', 'refresh_site_silos', False, 'POST', '/refreshSilos', {}),
    ('C15', 'list_last_known_good', False, 'GET', '/lastKnownGood', {}),
    ('C16', 'show_last_known_good', False, 'GET', '/lastKnownGood/default', {}),
    ('C17', 'mark_last_known_good', False, 'POST', '/lastKnownGood/default/mark', {}),
    ('C18', 'list_managed_traffic', False, 'GET', '/managedTrafficConfig', {}),
    ('C19', 'show_managed_traffic', False, 'GET', '/managedTrafficConfig/default', {}),
    ('C20', 'update_managed_traffic', False, 'PUT', '/managedTrafficConfig/default', {'traffic_mode': 'Active'}),
    ('C21', 'list_managed_traffic_metrics', False, 'GET', '/managedTrafficConfig/default/metrics', {}),
    ('C22', 'show_silo_vnet_integration', False, 'GET', '/silos/backup/virtualNetworkConnections/virtualNetwork',
     {'silo': 'backup'}),
    ('C23', 'add_silo_vnet_integration', False, 'PUT', '/silos/backup/virtualNetworkConnections/virtualNetwork',
     {'silo': 'backup', 'subnet': '/subscriptions/sub/subnets/net'}),
    ('C24', 'update_silo_vnet_integration', False, 'PATCH', '/silos/backup/virtualNetworkConnections/virtualNetwork',
     {'silo': 'backup', 'subnet': '/subscriptions/sub/subnets/net'}),
    ('C25', 'remove_silo_vnet_integration', False, 'DELETE', '/silos/backup/virtualNetworkConnections/virtualNetwork',
     {'silo': 'backup'}),
)

PAGED_COLLECTION_APIS = {
    'P02', 'P09', 'P11', 'P21', 'P23', 'P27', 'P29', 'P32', 'P40',
    'P43', 'P44', 'P47', 'P62', 'P64', 'P65', 'P66', 'P82', 'P83',
}


class ActiveBackupCommandTests(unittest.TestCase):

    def setUp(self):
        self.ctx = cli_context()
        self.cmd = type('Command', (), {'cli_ctx': self.ctx})()
        self.client = ActiveBackupClient(self.ctx, 'group', 'primary', subscription='subscription')
        self.client_patch = patch(MODULE + '._client', return_value=self.client)
        self.client_patch.start()
        self.addCleanup(self.client_patch.stop)
        self.request_patch = patch.object(self.client, 'request', return_value=response(payload={'value': []}))
        self.request = self.request_patch.start()
        self.addCleanup(self.request_patch.stop)

    def test_all_25_resource_action_mappings(self):
        self.assertEqual([case[0] for case in RESOURCE_CASES], ['C{:02}'.format(i) for i in range(1, 26)])
        for key, handler, plan, method, suffix, kwargs in RESOURCE_CASES:
            client = ActiveBackupClient(self.ctx, 'group', 'primary',
                                        'serverfarms' if plan else 'sites', subscription='subscription')
            result = response(204) if key in ('C14', 'C25') else response(payload={
                'location': 'westus2', 'properties': {'primaryLocation': 'eastus'}, 'value': []})
            with self.subTest(api=key), patch(MODULE + '._client', return_value=client), \
                    patch.object(client, 'request', return_value=result) as request, patch(MODULE + '.logger'):
                getattr(commands, handler)(self.cmd, 'group', 'primary', **kwargs)
                call = request.call_args
                self.assertEqual(call.args[0], method)
                self.assertEqual(urlsplit(call.args[1]).path, client.parent + suffix)
                self.assertEqual(request.call_count, 2 if key in ('C04', 'C11') else 1)

    def test_all_84_pass_through_methods_have_exact_route_and_no_preflight(self):
        self.assertEqual([case[0] for case in PASS_THROUGH_CASES], ['P{:02}'.format(i) for i in range(1, 85)])
        registered = {handler for entries in COMMAND_GROUPS.values() for _, handler in entries}
        for key, handler, method, suffix, kwargs in PASS_THROUGH_CASES:
            with self.subTest(api=key, handler=handler), \
                    patch.object(self.client, 'consume', return_value={'file': 'out'}) as consume, \
                    patch(MODULE + '._primary_location') as primary:
                self.request.reset_mock()
                getattr(commands, handler)(self.cmd, 'group', 'primary', 'backup', **kwargs)
                call = consume.call_args if consume.called else self.request.call_args
                self.assertIsNotNone(call)
                self.assertEqual(call.args[0], method)
                self.assertEqual(urlsplit(call.args[1]).path, self.client.resource('backup') + suffix)
                self.assertEqual(self.request.call_count + consume.call_count, 1)
                primary.assert_not_called()
                self.assertIn(handler, registered)

    def test_instance_qualified_process_and_live_log_routes(self):
        for _, handler, method, suffix, kwargs in PASS_THROUGH_CASES:
            if not (suffix.startswith('/processes/') or handler in ('restart_silo_container', 'tail_silo_logs')):
                continue
            with self.subTest(handler=handler), patch.object(self.client, 'consume') as consume:
                self.request.reset_mock()
                getattr(commands, handler)(self.cmd, 'group', 'primary', 'backup',
                                           **dict(kwargs, instance='worker'))
                call = consume.call_args if consume.called else self.request.call_args
                self.assertEqual(call.args[0], method)
                self.assertEqual(urlsplit(call.args[1]).path,
                                 self.client.resource('backup') + '/instances/worker' + suffix)

    def test_every_paged_pass_through_returns_all_collection_items(self):
        for key, handler, _, suffix, kwargs in PASS_THROUGH_CASES:
            if key not in PAGED_COLLECTION_APIS:
                continue
            with self.subTest(api=key):
                self.request.reset_mock()
                path = self.client.resource('backup') + suffix
                next_link = path + '?api-version=' + API_VERSION + '&page=2'
                items = [{'name': 'first', 'properties': {'unknownField': 1}},
                         {'name': 'second', 'properties': {'unknownField': 2}}]
                self.request.side_effect = [
                    response(payload={'value': items[:1], 'nextLink': next_link}),
                    response(payload={'value': items[1:]})]
                self.assertEqual(getattr(commands, handler)(self.cmd, 'group', 'primary', 'backup', **kwargs), items)
                self.assertEqual(self.request.call_count, 2)
                self.assertEqual(self.request.call_args.args, ('GET', self.client.url(next_link)))

    def test_collection_pagination_failure_does_not_return_partial_success(self):
        self.request.side_effect = [
            response(payload={'value': [{'name': 'first'}], 'nextLink': self.client.resource('backup') + '?page=2'}),
            ResourceNotFoundError('Second page missing')]
        with self.assertRaises(ResourceNotFoundError):
            commands.list_silo_instances(self.cmd, 'group', 'primary', 'backup')
        self.assertEqual(self.request.call_count, 2)

    def test_collection_query_parameters_are_not_reapplied_to_next_link(self):
        next_link = self.client.resource('backup') + '/metrics?api-version=' + API_VERSION + '&page=2'
        self.request.side_effect = [
            response(payload={'value': [], 'nextLink': next_link}), response(payload={'value': []})]
        self.assertEqual(commands.list_silo_metrics(
            self.cmd, 'group', 'primary', 'backup', names=['Requests'], time_grain='PT1H',
            details=False, slot_view=True), [])
        first_query = parse_qs(urlsplit(self.request.call_args_list[0].args[1]).query)
        self.assertIn("name.value eq 'Requests'", first_query['$filter'][0])
        self.assertEqual(first_query['details'], ['false'])
        self.assertEqual(first_query['slotView'], ['true'])
        self.assertEqual(parse_qs(urlsplit(self.request.call_args.args[1]).query),
                         {'api-version': [API_VERSION], 'page': ['2']})

    def test_property_bags_and_startup_log_wrappers_are_not_flattened(self):
        bag = {'properties': {'value': 'setting value', 'other': False}, 'unknownField': 'preserved'}
        startup = {'files': [{'name': 'startup.log'}], 'nextToken': 'preserved'}
        for handler, payload in (
                (commands.list_silo_appsettings, bag), (commands.list_silo_storage_accounts, bag),
                (commands.list_silo_connection_strings, bag), (commands.list_silo_metadata, bag),
                (commands.list_silo_startup_logs, startup)):
            with self.subTest(handler=handler.__name__):
                self.request.reset_mock()
                self.request.return_value = response(payload=payload)
                self.assertEqual(handler(self.cmd, 'group', 'primary', 'backup'), payload)
                self.request.assert_called_once()

    def test_extension_verbs_bodies_and_path_validation(self):
        for method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD'):
            commands.invoke_silo_extension(self.cmd, 'group', 'primary', 'backup', 'worker', 'api/settings',
                                           method=method, body='[1,2]')
            self.assertEqual(self.request.call_args.args[0], method)
            self.assertEqual(self.request.call_args.args[2], [1, 2])
        for path in ('../primary', '%2e%2e/primary', 'api/%252e%252e', '/api/x', 'api/x?y=z',
                     'api\\x', 'api/%2fescape', 'https://other.test/api'):
            with self.subTest(path=path), self.assertRaises(InvalidArgumentValueError):
                commands.invoke_silo_extension(self.cmd, 'group', 'primary', 'backup', 'worker', path)
        commands.invoke_silo_extension(self.cmd, 'group', 'primary', 'backup', 'worker', 'api/settings',
                                       uri_parameters=['item=one', 'item=two'])
        self.assertEqual(self.request.call_args.args[3], {'item': ['one', 'two']})
        with self.assertRaises(InvalidArgumentValueError):
            commands.invoke_silo_extension(self.cmd, 'group', 'primary', 'backup', 'worker', 'api/settings',
                                           uri_parameters=['api-version=old'])
        commands.invoke_silo_extension(self.cmd, 'group', 'primary', 'backup', 'worker', 'api/settings',
                                       method='POST', body='null')
        self.assertEqual(self.request.call_args.args[2], b'null')

    def test_normal_not_found_is_not_empty_success_or_primary_fallback(self):
        self.request.side_effect = ResourceNotFoundError('Silo not found')
        with self.assertRaises(ResourceNotFoundError):
            commands.show_silo_config(self.cmd, 'group', 'primary', 'backup')
        self.request.assert_called_once()

    def test_plan_creation_and_explicit_false(self):
        commands.create_plan_silo(self.cmd, 'group', 'primary', 'backup', 'westus2',
                                  primary_location='eastus', number_of_workers=2, zone_redundant='false')
        self.assertEqual(self.request.call_args.args[2], {
            'location': 'westus2', 'properties': {
                'name': 'backup', 'primaryLocation': 'eastus',
                'instanceNumberOverride': 2, 'zoneRedundantOverride': False}})
        self.request.assert_called_once()

    def test_site_creation_does_not_create_plan_or_invent_overrides(self):
        commands.create_site_silo(self.cmd, 'group', 'primary', 'backup', 'westus2',
                                  primary_location='eastus', traffic_mode='Active')
        self.assertEqual(self.request.call_args.args[2], {
            'location': 'westus2', 'properties': {
                'name': 'backup', 'primaryLocation': 'eastus', 'trafficMode': 'Active'}})
        self.request.assert_called_once()

    def test_create_resolves_primary_location_only_when_omitted(self):
        with patch(MODULE + '._primary_location', return_value='eastus') as primary:
            commands.create_site_silo(self.cmd, 'group', 'primary', 'backup', 'westus2', traffic_mode='Active')
        primary.assert_called_once_with(self.cmd, 'group', 'primary', False)
        self.assertEqual(self.request.call_args.args[2]['properties']['primaryLocation'], 'eastus')

    def test_update_reads_silo_and_sends_only_writable_requested_fields(self):
        self.request.side_effect = [
            response(payload={'location': 'westus2', 'properties': {
                'primaryLocation': 'eastus', 'revisionNumber': 8, 'provisioningState': 'Succeeded',
                'followLastKnownGood': True}}),
            response(payload={'id': 'silo'})]
        commands.update_site_silo(self.cmd, 'group', 'primary', 'backup', endpoint_status='Disabled')
        self.assertEqual(self.request.call_args.args[2], {
            'location': 'westus2', 'properties': {
                'name': 'backup', 'primaryLocation': 'eastus', 'endpointStatus': 'Disabled'}})
        self.assertEqual(self.request.call_count, 2)

    def test_worker_override_boundaries(self):
        for value in (0, -1, 31):
            with self.subTest(value=value), self.assertRaises(InvalidArgumentValueError):
                commands.create_plan_silo(self.cmd, 'group', 'primary', 'backup', 'westus2',
                                          primary_location='eastus', number_of_workers=value)
        self.request.assert_not_called()
        for value in (1, 30):
            commands.create_plan_silo(self.cmd, 'group', 'primary', 'backup', 'westus2',
                                      primary_location='eastus', number_of_workers=value)
            self.assertEqual(self.request.call_args.args[2]['properties']['instanceNumberOverride'], value)

    def test_refresh_204_is_one_request_and_notice_without_revision_wait(self):
        self.request.return_value = response(204)
        with patch(MODULE + '.logger') as logger:
            self.assertIsNone(commands.refresh_site_silos(self.cmd, 'group', 'primary'))
        self.request.assert_called_once_with('POST', self.client.parent + '/refreshSilos')
        logger.warning.assert_called_once()
        self.assertIn('accepted', logger.warning.call_args.args[0])
        self.assertNotIn('revision X', logger.warning.call_args.args[0])

    def test_refresh_conflict_does_not_report_acceptance(self):
        for status in (400, 409):
            error = AzureResponseError('Refresh rejected')
            error.response = response(status)
            self.request.side_effect = error
            with self.subTest(status=status), patch(MODULE + '.logger') as logger, \
                    self.assertRaises(AzureResponseError):
                commands.refresh_site_silos(self.cmd, 'group', 'primary')
            logger.warning.assert_not_called()

    def test_managed_traffic_mode_only_and_partial_endpoint_overlay(self):
        commands.update_managed_traffic(self.cmd, 'group', 'primary', traffic_mode='Passive')
        self.assertEqual(self.request.call_args.args[2], {'properties': {'trafficMode': 'Passive'}})
        commands.update_managed_traffic(self.cmd, 'group', 'primary',
                                        endpoints='[{"region":"westus2","weight":3}]')
        self.assertEqual(self.request.call_args.args[2], {
            'properties': {'endpoints': [{'region': 'westus2', 'weight': 3}]}})
        for endpoints in ('[{"weight":2}]', '[{"region":"x","weight":0}]',
                          '[{"region":"x","priority":true}]', '[{"region":"x","isWeightAutoComputed":true}]'):
            with self.subTest(endpoints=endpoints), self.assertRaises(InvalidArgumentValueError):
                commands.update_managed_traffic(self.cmd, 'group', 'primary', endpoints=endpoints)

    def test_traffic_expansion_only_on_collection(self):
        commands.list_managed_traffic(self.cmd, 'group', 'primary', expand_endpoints=True)
        self.assertIn('%24expand=endpoints', self.request.call_args.args[1])
        commands.show_managed_traffic(self.cmd, 'group', 'primary')
        self.assertEqual(self.request.call_args.args, ('GET', self.client.parent + '/managedTrafficConfig/default'))

    def test_last_known_good_mark_does_not_refresh(self):
        commands.mark_last_known_good(self.cmd, 'group', 'primary')
        self.request.assert_called_once_with('POST', self.client.parent + '/lastKnownGood/default/mark')

    def test_networking_exact_routes_verbs_and_body(self):
        for handler, method in ((commands.add_silo_vnet_integration, 'PUT'),
                                (commands.update_silo_vnet_integration, 'PATCH')):
            with self.subTest(method=method):
                handler(self.cmd, 'group', 'primary', 'backup', subnet='/subscriptions/sub/subnets/net')
                self.assertEqual(self.request.call_args.args[:3], (
                    method, self.client.resource('backup') + '/virtualNetworkConnections/virtualNetwork',
                    {'properties': {'subnetResourceId': '/subscriptions/sub/subnets/net'}}))
        self.request.return_value = response(204)
        self.assertIsNone(commands.remove_silo_vnet_integration(self.cmd, 'group', 'primary', 'backup'))

    def test_startup_log_queries_and_explicit_false_flags(self):
        commands.list_silo_startup_logs(self.cmd, 'group', 'primary', 'backup',
                                        log_type='All', instance='worker', latest=False)
        self.assertEqual(self.request.call_args.args[3], {
            'type': 'All', 'targetSiteInstance': 'worker', 'latest': False})
        commands.restart_site_silo(self.cmd, 'group', 'primary', 'backup',
                                   soft_restart=False, synchronous=False)
        self.assertEqual(self.request.call_args.args[3], {'softRestart': False, 'synchronous': False})

    def test_metric_filters_and_service_validation(self):
        query = commands._metric_query('2026-10-18T00:00:00Z', None, 'PT1H', ['Requests'])
        self.assertIn("timeGrain eq duration'PT1H'", query['$filter'])
        self.assertIn("name.value eq 'Requests'", query['$filter'])
        with self.assertRaises(InvalidArgumentValueError):
            commands._metric_query(start_time='x', filter_string='x')

    def test_table_preserves_degraded_and_no_wait_receipt(self):
        row = commands.silo_table({'name': 'backup', 'properties': {
            'provisioningState': 'Degraded', 'revisionNumber': 3, 'errorCode': 'SyncFailed'}})[0]
        self.assertEqual(row['State'], 'Degraded')
        self.assertEqual(row['Error'], 'SyncFailed')
        receipt = commands.silo_table({'status': 'Accepted', 'operationId': 'op', 'resourceId': 'id'})[0]
        self.assertEqual(receipt['Status'], 'Accepted')

    def test_all_registered_handlers_and_help_exist(self):
        from knack.help_files import helps
        seen = set()
        for group, entries in COMMAND_GROUPS.items():
            for verb, handler in entries:
                command = group + ' ' + verb
                with self.subTest(command=command):
                    self.assertNotIn(command, seen)
                    seen.add(command)
                    self.assertTrue(callable(getattr(commands, handler)))
                    self.assertIn(command, helps)
                    self.assertIn('examples:', helps[command])
                    self.assertIn('cmd', inspect.signature(getattr(commands, handler)).parameters)
        self.assertEqual(len(seen), 104)


class ActiveBackupHelpTests(unittest.TestCase):

    @staticmethod
    def invoke_json(arguments):
        return ActiveBackupHelpTests.invoke_output(arguments)

    @staticmethod
    def invoke_output(arguments, output_format='json'):
        from azure.cli.core import get_default_cli
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                exit_code = get_default_cli().invoke(arguments + ['--output', output_format], out_file=stdout)
            except SystemExit as ex:
                exit_code = ex.code
        if exit_code:
            raise AssertionError(stderr.getvalue())
        return exit_code, stdout.getvalue()

    @staticmethod
    def invoke(arguments):
        from azure.cli.core import get_default_cli
        if '--help' not in arguments:
            arguments = arguments + ['--output', 'none']
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            try:
                return get_default_cli().invoke(arguments)
            except SystemExit as ex:
                return ex.code

    def test_every_command_loads_help(self):
        for group, entries in COMMAND_GROUPS.items():
            for verb, _ in entries:
                command = group + ' ' + verb
                with self.subTest(command=command):
                    self.assertEqual(self.invoke(command.split() + ['--help']), 0)

    def test_named_command_executes_exact_silo_request(self):
        client = ActiveBackupClient(cli_context(), 'group', 'primary', subscription='sub')
        with patch(MODULE + '._client', return_value=client), \
                patch.object(client, 'request', return_value=response(payload={'id': 'silo'})) as request:
            self.assertEqual(self.invoke(
                'webapp silo config show -g group -n primary --silo backup'.split()), 0)
            self.assertEqual(request.call_args.args[:2], ('GET', client.resource('backup') + '/config/web'))

    def test_cli_updates_ignore_configured_location_defaults(self):
        for group, resource_type in (('appservice plan silo', 'serverfarms'), ('webapp silo', 'sites')):
            for explicit_location in (False, True):
                with self.subTest(group=group, explicit_location=explicit_location):
                    client = ActiveBackupClient(
                        cli_context(), 'group', 'primary', resource_type, subscription='sub')
                    resource = {'location': 'westus2', 'properties': {'primaryLocation': 'eastus'}}
                    arguments = (group + ' update -g group -n primary --silo backup').split()
                    arguments += (['--number-of-workers', '2'] if resource_type == 'serverfarms'
                                  else ['--endpoint-status', 'Disabled'])
                    if explicit_location:
                        arguments += ['--location', 'westus2']
                    with patch.dict('os.environ', {'AZURE_DEFAULTS_LOCATION': 'eastus'}), \
                            patch(MODULE + '._client', return_value=client), \
                            patch.object(client, 'request', return_value=response(payload=resource)) as request:
                        self.assertEqual(self.invoke(arguments), 0)
                    self.assertEqual(request.call_count, 2)
                    self.assertEqual(request.call_args.args[0], 'PUT')
                    self.assertEqual(request.call_args.args[2]['location'], 'westus2')

    def test_cli_creates_require_an_explicit_silo_location_despite_defaults(self):
        for group in ('appservice plan silo', 'webapp silo'):
            with self.subTest(group=group), \
                    patch.dict('os.environ', {'AZURE_DEFAULTS_LOCATION': 'eastus'}), \
                    patch(MODULE + '._client') as factory:
                self.assertNotEqual(self.invoke(
                    (group + ' create -g group -n primary --silo backup --primary-location eastus').split()), 0)
                factory.assert_not_called()

    def test_cli_collection_commands_return_arrays_from_all_pages(self):
        registered = {handler: group + ' ' + verb
                      for group, entries in COMMAND_GROUPS.items() for verb, handler in entries}
        for key, handler, _, suffix, kwargs in PASS_THROUGH_CASES:
            if key not in PAGED_COLLECTION_APIS:
                continue
            with self.subTest(api=key):
                client = ActiveBackupClient(cli_context(), 'group', 'primary', subscription='sub')
                arguments = registered[handler].split() + ['-g', 'group', '-n', 'primary', '--silo', 'backup']
                for key_name, value in kwargs.items():
                    arguments += ['--' + key_name.replace('_', '-'), value]
                with patch(MODULE + '._client', return_value=client), \
                        patch.object(client, 'request', side_effect=[
                            response(payload={'value': [{'name': 'first'}],
                                              'nextLink': client.resource('backup') + suffix + '?page=2'}),
                            response(payload={'value': [{'name': 'second'}]})]) as request:
                    _, output = self.invoke_json(arguments)
                self.assertEqual(json.loads(output), [{'name': 'first'}, {'name': 'second'}])
                self.assertEqual(request.call_count, 2)

    def test_cli_collection_table_and_list_queries_include_all_pages(self):
        for output_format, query in (('table', None), ('json', '[].name')):
            with self.subTest(output_format=output_format, query=query):
                client = ActiveBackupClient(cli_context(), 'group', 'primary', subscription='sub')
                arguments = 'webapp silo instance list -g group -n primary --silo backup'.split()
                if query:
                    arguments += ['--query', query]
                with patch(MODULE + '._client', return_value=client), \
                        patch.object(client, 'request', side_effect=[
                            response(payload={'value': [{'name': 'first'}],
                                              'nextLink': client.resource('backup') + '/instances?page=2'}),
                            response(payload={'value': [{'name': 'second'}]})]) as request:
                    _, output = self.invoke_output(arguments, output_format)
                self.assertEqual(request.call_count, 2)
                if query:
                    self.assertEqual(json.loads(output), ['first', 'second'])
                else:
                    self.assertIn('first', output)
                    self.assertIn('second', output)

    def test_nested_ids_are_typed_and_do_not_silently_override_names(self):
        resource_id = (
            '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/group/'
            'providers/Microsoft.Web/sites/primary/silos/backup')
        client = ActiveBackupClient(cli_context(), 'group', 'primary', subscription='sub')
        with patch(MODULE + '._client', return_value=client) as factory, \
                patch.object(client, 'request', return_value=response(payload={'id': 'silo'})) as request:
            self.assertEqual(self.invoke(['webapp', 'silo', 'show', '--ids', resource_id]), 0)
            self.assertEqual(factory.call_args.args[1:3], ('group', 'primary'))
            self.assertEqual(request.call_args.args[:2], ('GET', client.resource('backup')))
            for arguments in (
                    ['webapp', 'silo', 'show', '--ids', resource_id, '-n', 'another'],
                    ['webapp', 'silo', 'show', '--ids', resource_id.replace('/sites/', '/serverfarms/')]):
                request.reset_mock()
                self.assertNotEqual(self.invoke(arguments), 0)
                request.assert_not_called()

    def test_cli_explicit_false_and_no_wait(self):
        client = ActiveBackupClient(cli_context(), 'group', 'primary', subscription='sub')
        initial = response(202, headers={'Location': client.resource('backup') + '/operationresults/op'})
        with patch(MODULE + '._client', return_value=client), \
                patch.object(client, 'request', return_value=initial) as request:
            self.assertEqual(self.invoke(
                'appservice plan silo create -g group -n primary --silo backup --location westus2 '
                '--primary-location eastus --zone-redundant false --no-wait'.split()), 0)
            self.assertIs(request.call_args.args[2]['properties']['zoneRedundantOverride'], False)
            request.assert_called_once()

    def test_cli_no_wait_receipts_are_not_discarded(self):
        for group, entries in COMMAND_GROUPS.items():
            for verb, handler_name in entries:
                parameters = inspect.signature(getattr(commands, handler_name)).parameters
                if 'no_wait' not in parameters:
                    continue
                with self.subTest(command=group + ' ' + verb):
                    client = ActiveBackupClient(
                        cli_context(), 'group', 'primary',
                        'serverfarms' if group.startswith('appservice plan') else 'sites',
                        subscription='sub')
                    resource_id = client.resource('backup')
                    poll = resource_id + '/operationresults/op'
                    initial = response(202, headers={'Location': poll})
                    existing = response(payload={
                        'id': resource_id, 'location': 'westus2',
                        'properties': {'primaryLocation': 'eastus'}})
                    arguments = (group + ' ' + verb).split() + [
                        '-g', 'group', '-n', 'primary', '--silo', 'backup', '--no-wait']
                    if 'location' in parameters:
                        arguments += ['--location', 'westus2', '--primary-location', 'eastus']
                    if verb == 'delete':
                        arguments += ['--yes']
                    with patch(MODULE + '._client', return_value=client), \
                            patch.object(client, 'request', side_effect=lambda method, *args, **kwargs:
                                         existing if method == 'GET' else initial) as request:
                        exit_code, output = self.invoke_json(arguments)
                    self.assertEqual(exit_code, 0)
                    self.assertTrue(output.strip(), 'The CLI discarded the no-wait operation receipt.')
                    receipt = json.loads(output)
                    self.assertEqual(receipt['status'], 'Accepted')
                    self.assertEqual(receipt['operationId'], 'op')
                    self.assertEqual(receipt['resourceId'], request.call_args.args[1])
                    self.assertEqual(receipt['operationUrl'], client.url(poll))
                    self.assertEqual(request.call_count, 2 if verb == 'update' else 1)

    def test_cli_no_wait_preserves_synchronous_resource_results(self):
        for group in ('appservice plan silo', 'webapp silo'):
            with self.subTest(command=group + ' create'):
                client = ActiveBackupClient(cli_context(), 'group', 'primary', subscription='sub')
                resource = {'id': client.resource('backup'), 'properties': {'provisioningState': 'Succeeded'}}
                with patch(MODULE + '._client', return_value=client), \
                        patch.object(client, 'request', return_value=response(payload=resource)) as request:
                    exit_code, output = self.invoke_json(
                        (group + ' create -g group -n primary --silo backup --location westus2 '
                         '--primary-location eastus --no-wait').split())
                self.assertEqual(exit_code, 0)
                self.assertTrue(output.strip(), 'The CLI discarded the synchronous resource result.')
                self.assertEqual(json.loads(output), dict(resource, resourceGroup='group'))
                request.assert_called_once()

    def test_cli_waited_writes_return_resource_json_not_operation_status(self):
        for group in ('appservice plan silo', 'webapp silo'):
            for verb in ('create', 'update'):
                with self.subTest(command=group + ' ' + verb):
                    client = ActiveBackupClient(
                        cli_context(), 'group', 'primary',
                        'serverfarms' if group.startswith('appservice plan') else 'sites',
                        subscription='sub')
                    resource_id = client.resource('backup')
                    existing = {'id': resource_id, 'location': 'westus2',
                                'properties': {'primaryLocation': 'eastus'}}
                    resource = dict(existing, properties={
                        'primaryLocation': 'eastus', 'provisioningState': 'Succeeded',
                        'instanceNumberOverride': 2, 'zoneRedundantOverride': False})
                    poll = resource_id + '/operationresults/op?azureAsyncOperation=1'
                    replies = [response(payload=existing)] if verb == 'update' else []
                    replies += [
                        response(202, headers={'Azure-AsyncOperation': poll, 'Retry-After': '0'}),
                        response(payload={'id': None, 'status': 'Succeeded', 'properties': None}),
                        response(payload=resource)]
                    with patch(MODULE + '._client', return_value=client), \
                            patch.object(client, 'request', side_effect=replies) as request, \
                            patch('azure.cli.command_modules.appservice._active_backup_client.time.sleep'):
                        exit_code, output = self.invoke_json(
                            (group + ' ' + verb + ' -g group -n primary --silo backup '
                             '--location westus2 --primary-location eastus').split())
                    self.assertEqual(exit_code, 0)
                    self.assertEqual(json.loads(output), dict(resource, resourceGroup='group'))
                    self.assertEqual(request.call_args.args, ('GET', resource_id))
                    self.assertEqual(request.call_count, 4 if verb == 'update' else 3)

    def test_cli_operation_show_uses_async_status_mode(self):
        for group, resource_type in (('appservice plan silo', 'serverfarms'), ('webapp silo', 'sites')):
            for state in ('InProgress', 'Succeeded'):
                with self.subTest(group=group, state=state):
                    client = ActiveBackupClient(
                        cli_context(), 'group', 'primary', resource_type, subscription='sub')
                    with patch(MODULE + '._client', return_value=client), \
                            patch.object(client, 'request', return_value=response(
                                payload={'id': None, 'status': state, 'properties': None})) as request:
                        exit_code, output = self.invoke_json(
                            (group + ' operation show -g group -n primary --silo backup --operation-id op').split())
                    self.assertEqual(exit_code, 0)
                    request.assert_called_once()
                    method, address = request.call_args.args
                    self.assertEqual(method, 'GET')
                    self.assertEqual(urlsplit(address).path, client.resource('backup') + '/operationresults/op')
                    self.assertEqual(parse_qs(urlsplit(address).query),
                                     {'api-version': [API_VERSION], 'azureAsyncOperation': ['1']})
                    self.assertEqual(json.loads(output),
                                     {'operationId': 'op', 'operationUrl': address, 'status': state})

    def test_cli_wait_uses_async_status_mode_without_resource_readback(self):
        for group, resource_type in (('appservice plan silo', 'serverfarms'), ('webapp silo', 'sites')):
            with self.subTest(group=group):
                client = ActiveBackupClient(cli_context(), 'group', 'primary', resource_type, subscription='sub')
                with patch(MODULE + '._client', return_value=client), \
                        patch.object(client, 'request', side_effect=[
                            response(202, headers={'Retry-After': '0'}),
                            response(payload={'id': None, 'status': 'Succeeded', 'properties': None})]) as request, \
                        patch('azure.cli.command_modules.appservice._active_backup_client.time.sleep'):
                    exit_code, output = self.invoke_json(
                        (group + ' wait -g group -n primary --silo backup --operation-id op').split())
                self.assertEqual(exit_code, 0)
                self.assertEqual(request.call_count, 2)
                for call in request.call_args_list:
                    self.assertEqual(call.args[0], 'GET')
                    self.assertEqual(urlsplit(call.args[1]).path, client.resource('backup') + '/operationresults/op')
                    self.assertEqual(parse_qs(urlsplit(call.args[1]).query),
                                     {'api-version': [API_VERSION], 'azureAsyncOperation': ['1']})
                self.assertEqual(json.loads(output),
                                 {'operationId': 'op', 'operationUrl': request.call_args.args[1], 'status': 'Succeeded'})

    def test_cli_operation_failures_are_not_masked(self):
        forbidden = AzureResponseError('Operation access denied.')
        forbidden.response = response(403)
        failures = [ResourceNotFoundError('Operation missing.'), forbidden] + [
            response(payload={'status': status, 'error': {'code': 'SiloFailed', 'message': 'Operation failed.'}})
            for status in ('Failed', 'Cancelled', 'TimedOut')]
        for group, resource_type in (('appservice plan silo', 'serverfarms'), ('webapp silo', 'sites')):
            for action in ('operation show', 'wait'):
                for failure in failures:
                    with self.subTest(group=group, action=action, failure=failure):
                        client = ActiveBackupClient(
                            cli_context(), 'group', 'primary', resource_type, subscription='sub')
                        with patch(MODULE + '._client', return_value=client), \
                                patch.object(client, 'request', side_effect=[failure]) as request:
                            exit_code = self.invoke(
                                (group + ' ' + action + ' -g group -n primary --silo origin --operation-id op').split())
                        self.assertNotEqual(exit_code, 0)
                        request.assert_called_once()
                        self.assertEqual(request.call_args.args[0], 'GET')
                        self.assertEqual(urlsplit(request.call_args.args[1]).path,
                                         client.resource('origin') + '/operationresults/op')
                        self.assertEqual(parse_qs(urlsplit(request.call_args.args[1]).query),
                                         {'api-version': [API_VERSION], 'azureAsyncOperation': ['1']})

    def test_cli_origin_show_reads_the_collection_after_point_404(self):
        client = ActiveBackupClient(cli_context(), 'group', 'primary',
                                    subscription='00000000-0000-0000-0000-000000000001')
        origin = client.resource('origin')
        resource = {'id': origin, 'name': 'origin', 'type': 'Microsoft.Web/sites/silos',
                    'location': 'eastus', 'properties': {'primaryLocation': 'eastus', 'endpointStatus': 'Enabled'}}
        with patch(MODULE + '._client', return_value=client), \
                patch.object(client, 'request', side_effect=[
                    ResourceNotFoundError('Origin point missing'), response(payload={'value': [resource]})]) as request, \
                patch('azure.cli.command_modules.appservice._active_backup_client.logger.warning') as warning:
            exit_code, output = self.invoke_json(['webapp', 'silo', 'show', '--ids', origin])
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output), dict(resource, resourceGroup='group'))
        self.assertEqual([call.args[:2] for call in request.call_args_list],
                         [('GET', origin), ('GET', client.url(client.resource()))])
        warning.assert_called_once()

    def test_cli_origin_update_uses_the_collection_before_and_after_async_write(self):
        client = ActiveBackupClient(cli_context(), 'group', 'primary', subscription='sub')
        origin = client.resource('origin')
        before = {'id': origin, 'name': 'origin', 'type': 'Microsoft.Web/sites/silos', 'location': 'eastus',
                  'properties': {'primaryLocation': 'eastus', 'endpointStatus': 'Enabled'}}
        after = dict(before, properties={'primaryLocation': 'eastus', 'endpointStatus': 'Disabled'})
        poll = origin + '/operationresults/op'
        with patch(MODULE + '._client', return_value=client), \
                patch.object(client, 'request', side_effect=[
                    ResourceNotFoundError('Point missing'), response(payload={'value': [before]}),
                    response(202, headers={'Azure-AsyncOperation': poll, 'Retry-After': '0'}),
                    response(payload={'id': None, 'status': 'Succeeded'}),
                    ResourceNotFoundError('Point still missing'), response(payload={'value': [after]})]) as request, \
                patch('azure.cli.command_modules.appservice._active_backup_client.time.sleep'), \
                patch('azure.cli.command_modules.appservice._active_backup_client.logger.warning') as warning:
            exit_code, output = self.invoke_json(
                'webapp silo update -g group -n primary --silo origin --endpoint-status Disabled'.split())
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output), dict(after, resourceGroup='group'))
        self.assertEqual(request.call_count, 6)
        self.assertEqual(request.call_args_list[2].args[:2], ('PUT', origin))
        expected_body = {
            'location': 'eastus',
            'properties': {'name': 'origin', 'primaryLocation': 'eastus', 'endpointStatus': 'Disabled'}}
        self.assertEqual(request.call_args_list[2].args[2], expected_body)
        warning.assert_called_once()

    def test_cli_origin_pass_through_does_not_use_collection_fallback(self):
        client = ActiveBackupClient(cli_context(), 'group', 'primary', subscription='sub')
        with patch(MODULE + '._client', return_value=client), \
                patch.object(client, 'request', side_effect=ResourceNotFoundError('Config missing')) as request:
            self.assertEqual(self.invoke(
                'webapp silo config show -g group -n primary --silo origin'.split()), 3)
        request.assert_called_once()
        self.assertEqual(request.call_args.args[:2], ('GET', client.resource('origin') + '/config/web'))

    def test_cli_not_found_has_show_exit_code(self):
        client = ActiveBackupClient(cli_context(), 'group', 'primary', subscription='sub')
        with patch(MODULE + '._client', return_value=client), \
                patch.object(client, 'request', side_effect=ResourceNotFoundError('Not found')) as request:
            self.assertEqual(self.invoke('webapp silo show -g group -n primary --silo backup'.split()), 3)
            request.assert_called_once()


if __name__ == '__main__':
    unittest.main()
