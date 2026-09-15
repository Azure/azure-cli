# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import inspect
import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from azure.cli.core import MainCommandsLoader, get_default_cli
from azure.cli.core.parser import AzCliCommandParser
from azure.cli.core.profiles import ResourceType
from azure.core.exceptions import HttpResponseError, ResourceExistsError
from knack.util import CLIError, CommandResultItem

from azure.cli.command_modules.acs import ContainerServiceCommandsLoader
from azure.cli.command_modules.acs.custom import _update_addons
from azure.cli.command_modules.acs.managed_cluster_decorator import AKSManagedClusterUpdateDecorator
from azure.mgmt.containerservice import ContainerServiceClient, models
from . import test_aks_commands as scenarios
from .mocks import MockCLI, MockCmd
from .test_aks_provisioning_retry import MockExecutionResult
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.patches import patch_main_exception_handler


def make_scenario():
    instance = object.__new__(scenarios.AzureKubernetesServiceScenarioTest)
    instance.kwargs = {}
    instance.cli_ctx = Mock()
    instance.is_live = True
    instance.in_recording = False
    instance.create_random_name = Mock(return_value='cluster')
    instance.generate_ssh_keys = Mock(return_value='public-key')
    instance._create_container_insights_workspace = Mock(return_value='/workspace')
    instance._create_azure_monitor_workspace = Mock(return_value='/amw')
    instance._get_versions = Mock(return_value=('1.34.1', '1.35.1'))
    instance._get_latest_official_version = Mock(return_value='1.35.1')
    instance._get_asm_supported_revision = Mock(return_value='asm-1-27')
    instance.cmd = Mock(return_value=MockExecutionResult({
        'addonProfiles': {'omsagent': {'config': {}}},
    }))
    return instance


def run_scenario(instance, name):
    inspect.unwrap(getattr(type(instance), name))(instance, 'rg', 'westcentralus')


def serialize_cluster_request(cluster):
    class RequestCaptured(Exception):
        pass

    with ContainerServiceClient(Mock(), 'sub') as client:
        with patch.object(client._client._pipeline, 'run', side_effect=RequestCaptured) as send:
            try:
                client.managed_clusters.begin_create_or_update('rg', 'cluster', cluster)
            except RequestCaptured:
                return json.loads(send.call_args.args[0].body)['properties']
    raise AssertionError('The SDK did not construct a managed cluster PUT')


class TestLiveScenarioSequencing(unittest.TestCase):
    def test_msi_workspace_does_not_provision_legacy_solution(self):
        instance = make_scenario()
        instance.cmd.side_effect = [
            MockExecutionResult({'id': '/workspace'}),
            HttpResponseError('(ResourceNotFound) The Container Insights solution was not found.'),
        ]
        result = type(instance)._create_container_insights_workspace(instance, 'rg', 'westcentralus')
        self.assertEqual(result, '/workspace')
        instance.cmd.assert_called_once()

    def test_monitoring_disable_waits_before_asserting_response(self):
        instance = make_scenario()
        output = instance.cmd.return_value
        instance.cmd.side_effect = lambda command, **kwargs: (
            MockExecutionResult(False) if '--query' in command else output
        )
        run_scenario(instance, 'test_aks_create_default_service_with_monitoring_addon_msi')
        calls = instance.cmd.call_args_list
        disable_index = next(i for i, call in enumerate(calls) if call.args[0].startswith('aks disable-addons'))
        self.assertFalse(calls[disable_index].kwargs.get('checks'))
        self.assertIn('aks wait', calls[disable_index + 1].args[0])
        self.assertTrue(any('omsagent.enabled' in call.args[0] for call in calls[disable_index + 2:]))

    def test_transit_encryption_waits_after_create(self):
        instance = make_scenario()
        run_scenario(instance, 'test_aks_update_with_acns_transit_encryption')
        self.assertIn('aks wait', instance.cmd.call_args_list[1].args[0])

    def test_localdns_waits_before_adding_pool(self):
        instance = make_scenario()
        instance.cmd.side_effect = [
            MockExecutionResult({}), MockExecutionResult({}),
            RuntimeError('stop before allocating pool'),
        ]
        with self.assertRaisesRegex(RuntimeError, 'stop before allocating pool'):
            run_scenario(instance, 'test_aks_nodepool_update_with_localdns_config')
        self.assertIn('aks wait', instance.cmd.call_args_list[1].args[0])

    def test_migration_uses_service_selected_size_in_live_run(self):
        instance = make_scenario()
        run_scenario(instance, 'test_aks_kubenet_to_cni_overlay_migration')
        command = instance.cmd.call_args_list[0].args[0].format(**instance.kwargs)
        self.assertNotIn('--node-vm-size', command)
        self.assertIn('--location=westcentralus', command)

    def test_ingress_gateway_scenario_needs_only_one_node_live(self):
        instance = make_scenario()
        run_scenario(instance, 'test_aks_azure_service_mesh_with_ingress_gateway')
        command = instance.cmd.call_args_list[0].args[0].format(**instance.kwargs)
        self.assertIn('--node-count=1', command)

    def test_all_metrics_creates_supply_explicit_recovery_update(self):
        for name in (
            'test_aks_create_with_azuremonitormetrics',
            'test_aks_create_with_control_plane_metrics',
            'test_aks_update_with_control_plane_metrics',
        ):
            with self.subTest(name=name):
                instance = make_scenario()
                instance._cmd_with_retried_create_recovery = Mock(side_effect=RuntimeError('stop at create'))
                with self.assertRaisesRegex(RuntimeError, 'stop at create'):
                    run_scenario(instance, name)
                recovery = instance._cmd_with_retried_create_recovery.call_args.kwargs['recovery_command']
                self.assertTrue(recovery.startswith('aks update '))
                self.assertIn('--enable-azure-monitor-metrics', recovery)
                self.assertIn('--azure-monitor-workspace-resource-id={amw_id}', recovery)
                if name == 'test_aks_create_with_control_plane_metrics':
                    self.assertIn('--enable-control-plane-metrics', recovery)
                if name == 'test_aks_create_with_azuremonitormetrics':
                    self.assertIn('--enable-windows-recording-rules', recovery)


class TestLiveConflictRecovery(unittest.TestCase):
    @patch.dict(os.environ, {'AZURE_CLI_TEST_OPERATION_MAX_RETRIES': '3'})
    @patch('time.sleep')
    @patch('azure.cli.testsdk.base.execute')
    def test_preempted_nodepool_operation_is_retried(self, execute, sleep):
        expected = MockExecutionResult({'provisioningState': 'Succeeded'})
        execute.side_effect = [
            HttpResponseError(
                '(AKSOperationPreempted) This operation has been preempted by another operation. '
                'Please retry later after the ongoing operation has finished.'
            ),
            expected,
        ]
        instance = make_scenario()
        self.assertIs(instance._execute_with_transient_conflict_retry('aks nodepool add', False), expected)
        sleep.assert_called_once()

    @patch.dict(os.environ, {'AZURE_CLI_TEST_OPERATION_MAX_RETRIES': '2'})
    @patch('time.sleep')
    @patch('azure.cli.testsdk.base.execute')
    def test_in_progress_sdk_error_remains_bounded(self, execute, sleep):
        execute.side_effect = ResourceExistsError(
            "(OperationNotAllowed) Operation is not allowed because there's an in-progress "
            "update managed cluster operation."
        )
        with self.assertRaises(ResourceExistsError):
            make_scenario()._execute_with_transient_conflict_retry('aks update', False)
        self.assertEqual(execute.call_count, 2)
        sleep.assert_called_once()

    @patch('azure.cli.testsdk.base.execute')
    def test_unrelated_operation_not_allowed_is_not_retried(self, execute):
        execute.side_effect = ResourceExistsError('(OperationNotAllowed) Feature is not enabled.')
        with self.assertRaises(ResourceExistsError):
            make_scenario()._execute_with_transient_conflict_retry('aks update', False)
        execute.assert_called_once()

    @patch.dict(os.environ, {'AZURE_CLI_TEST_OPERATION_MAX_RETRIES': '3'})
    @patch('time.sleep')
    @patch('azure.cli.testsdk.base.execute')
    def test_metrics_recovery_resumes_postprocessing_instead_of_show(self, execute, _sleep):
        instance = make_scenario()
        instance._allow_retried_create_recovery = True
        instance._retried_create_recovery_command = 'aks update -g rg -n cluster --enable-azure-monitor-metrics'
        expected = MockExecutionResult({'azureMonitorProfile': {'metrics': {'enabled': True}}})
        execute.side_effect = [
            CLIError('Another operation is in progress.'),
            CLIError("The cluster 'cluster' already exists."),
            expected,
        ]
        instance._execute_with_transient_conflict_retry('aks create -g rg -n cluster', False)
        execute.assert_called_with(
            instance.cli_ctx, instance._retried_create_recovery_command, expect_failure=False
        )


class TestTestsdkExceptionDispatch(unittest.TestCase):
    def setUp(self):
        config = tempfile.TemporaryDirectory()
        self.addCleanup(config.cleanup)
        env = patch.dict(os.environ, {
            'AZURE_CONFIG_DIR': config.name,
            'AZURE_CORE_COLLECT_TELEMETRY': '0',
        })
        env.start()
        self.addCleanup(env.stop)
        patch_main_exception_handler(self)
        self.cli = get_default_cli()

    @patch('azure.cli.core.commands.AzCliCommandInvoker.execute')
    def test_real_execute_unwraps_cli_exception_handler(self, invoke):
        for error in (
            CLIError('Another operation is in progress.'),
            ResourceExistsError("(OperationNotAllowed) Operation is not allowed because there's an in-progress update."),
            HttpResponseError('(AKSOperationPreempted) Please retry after the ongoing operation has finished.'),
        ):
            with self.subTest(error_type=type(error).__name__):
                invoke.side_effect = error
                with self.assertRaises(type(error)) as raised:
                    execute(self.cli, 'aks update -g rg -n cluster')
                self.assertIs(raised.exception, error)

    @patch.dict(os.environ, {'AZURE_CLI_TEST_OPERATION_MAX_RETRIES': '2'})
    @patch('time.sleep')
    @patch('azure.cli.core.commands.AzCliCommandInvoker.execute')
    def test_retry_receives_unwrapped_error_from_real_execute(self, invoke, sleep):
        for error in (
            ResourceExistsError("(OperationNotAllowed) Operation is not allowed because there's an in-progress update."),
            HttpResponseError('(AKSOperationPreempted) Please retry after the ongoing operation has finished.'),
        ):
            with self.subTest(error_type=type(error).__name__):
                invoke.reset_mock()
                sleep.reset_mock()
                results = iter([error, CommandResultItem({'provisioningState': 'Succeeded'})])

                def invoke_command(*args, **kwargs):
                    self.cli.invocation.data['output'] = 'json'
                    result = next(results)
                    if isinstance(result, Exception):
                        raise result
                    return result

                invoke.side_effect = invoke_command
                instance = make_scenario()
                instance.cli_ctx = self.cli
                result = instance._execute_with_transient_conflict_retry('aks update -g rg -n cluster', False)
                self.assertEqual(result.get_output_in_json()['provisioningState'], 'Succeeded')
                self.assertEqual(invoke.call_count, 2)
                sleep.assert_called_once()

    @patch('time.sleep')
    @patch('azure.cli.core.commands.AzCliCommandInvoker.execute')
    def test_expected_failure_is_not_retried_by_real_execute(self, invoke, sleep):
        invoke.side_effect = HttpResponseError('(AKSOperationPreempted) An operation was preempted.')
        instance = make_scenario()
        instance.cli_ctx = self.cli
        result = instance._execute_with_transient_conflict_retry('aks update -g rg -n cluster', True)
        self.assertEqual(result.exit_code, 1)
        invoke.assert_called_once()
        sleep.assert_not_called()


class TestZoneCapabilityPreflight(unittest.TestCase):
    def test_non_zonal_region_is_skipped_before_create(self):
        instance = make_scenario()
        instance.cmd.return_value = MockExecutionResult([
            {'locationInfo': [{'location': 'westcentralus', 'zones': None}]},
            {'locationInfo': None},
        ])
        with self.assertRaisesRegex(unittest.SkipTest, 'westcentralus'):
            instance._require_availability_zones('westcentralus', ['1', '2', '3'])
        self.assertEqual(instance.cmd.call_count, 1)

    def test_supported_region_runs_without_relocation(self):
        instance = make_scenario()
        instance.cmd.return_value = MockExecutionResult([
            {'locationInfo': [{'location': 'westus2', 'zones': ['1', '2', '3']}]},
        ])
        instance._require_availability_zones('westus2', ['1', '2', '3'])
        self.assertIn('--location westus2', instance.cmd.call_args.args[0])

    def test_empty_catalog_is_not_silently_skipped(self):
        instance = make_scenario()
        instance.cmd.return_value = MockExecutionResult([])
        with self.assertRaisesRegex(AssertionError, 'capabilities'):
            instance._require_availability_zones('westcentralus', ['1'])

    def test_replay_issues_no_new_request(self):
        instance = make_scenario()
        instance.is_live = False
        instance._require_availability_zones('westcentralus', ['1'])
        instance.cmd.assert_not_called()

    def test_zone_scenarios_check_capabilities_before_cluster_creation(self):
        for name in ('test_aks_availability_zones_msi', 'test_aks_enable_utlra_ssd', 'test_aks_machine_cmds'):
            with self.subTest(name=name):
                instance = make_scenario()
                instance.cmd.return_value = MockExecutionResult([
                    {'locationInfo': [{'location': 'westcentralus', 'zones': []}]},
                ])
                with self.assertRaises(unittest.SkipTest):
                    run_scenario(instance, name)
                instance.cmd.assert_called_once()
                self.assertTrue(instance.cmd.call_args.args[0].startswith('vm list-skus'))


class TestFlowLogCommandPayload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cli = get_default_cli()
        main = MainCommandsLoader(cli)
        cli.invocation = Mock(data={'command_string': 'aks update'}, commands_loader=main)
        loader = ContainerServiceCommandsLoader(cli)
        loader.load_command_table(['aks', 'update'])
        main.command_table = {'aks update': loader.command_table['aks update']}
        main.cmd_to_loader_map = {'aks update': [loader]}
        main.load_arguments('aks update')
        cls.parser = AzCliCommandParser(cli_ctx=cli)
        cls.parser.load_command_table(main)

    def test_disable_then_unrelated_update_preserves_disabled_wire_value(self):
        cmd = MockCmd(MockCLI())
        client = Mock()
        for flags in (['--disable-container-network-logs'], ['--enable-high-log-scale-mode']):
            raw = vars(self.parser.parse_args(['aks', 'update', '-g', 'rg', '-n', 'cluster'] + flags))
            decorator = AKSManagedClusterUpdateDecorator(cmd, client, raw, ResourceType.MGMT_CONTAINERSERVICE)
            if flags[0] == '--disable-container-network-logs':
                cluster = decorator.models.ManagedCluster(
                    location='westus2',
                    addon_profiles={'omsagent': decorator.models.ManagedClusterAddonProfile(
                        enabled=True,
                        config={'enableRetinaNetworkFlags': 'true', 'useAADAuth': 'true'},
                    )},
                )
            decorator.context.attach_mc(cluster)
            decorator.update_monitoring_profile_flow_logs(cluster)
            decorator.update_addon_profiles(cluster)
            payload = serialize_cluster_request(cluster)
            self.assertEqual(
                payload['addonProfiles']['omsagent']['config']['enableRetinaNetworkFlags'].lower(),
                'false',
            )

    def test_flow_flags_update_existing_canonical_profile(self):
        for flag, initial, expected in (
            ('--disable-container-network-logs', 'Enabled', 'Disabled'),
            ('--enable-container-network-logs', 'Disabled', 'Enabled'),
        ):
            with self.subTest(flag=flag):
                raw = vars(self.parser.parse_args(['aks', 'update', '-g', 'rg', '-n', 'cluster', flag]))
                decorator = AKSManagedClusterUpdateDecorator(
                    MockCmd(MockCLI()), Mock(), raw, ResourceType.MGMT_CONTAINERSERVICE
                )
                cluster = models.ManagedCluster(
                    location='westus2',
                    network_profile=models.ContainerServiceNetworkProfile(
                        network_dataplane='cilium', advanced_networking=models.AdvancedNetworking(enabled=True),
                    ),
                    addon_profiles={'omsagent': models.ManagedClusterAddonProfile(
                        enabled=True, config={'enableRetinaNetworkFlags': str(initial == 'Enabled')},
                    )},
                    azure_monitor_profile=models.ManagedClusterAzureMonitorProfile(
                        container_insights=models.ManagedClusterAzureMonitorProfileContainerInsights(
                            enabled=True, container_network_logs=initial,
                        ),
                        metrics=models.ManagedClusterAzureMonitorProfileMetrics(enabled=True),
                    ),
                )
                decorator.context.attach_mc(cluster)
                decorator.update_monitoring_profile_flow_logs(cluster)
                payload = serialize_cluster_request(cluster)
                self.assertEqual(payload['azureMonitorProfile']['containerInsights']['containerNetworkLogs'], expected)
                self.assertTrue(payload['azureMonitorProfile']['metrics']['enabled'])
                self.assertEqual(
                    payload['addonProfiles']['omsagent']['config']['enableRetinaNetworkFlags'].lower(),
                    str(expected == 'Enabled').lower(),
                )

    def test_monitoring_disable_reenable_updates_existing_canonical_profile(self):
        workspace = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/workspace'
        cluster = models.ManagedCluster(
            location='westus2',
            addon_profiles={'omsagent': models.ManagedClusterAddonProfile(
                enabled=True, config={'logAnalyticsWorkspaceResourceID': workspace},
            )},
            azure_monitor_profile=models.ManagedClusterAzureMonitorProfile(
                container_insights=models.ManagedClusterAzureMonitorProfileContainerInsights(
                    enabled=True, log_analytics_workspace_resource_id=workspace, container_network_logs='Enabled',
                ),
                metrics=models.ManagedClusterAzureMonitorProfileMetrics(enabled=True),
            ),
        )
        for enable in (False, True):
            with self.subTest(enable=enable):
                _update_addons(
                    MockCmd(MockCLI()), cluster, 'sub', 'rg', 'cluster', 'monitoring', enable,
                    workspace_resource_id=workspace,
                )
                profile = serialize_cluster_request(cluster)['azureMonitorProfile']
                self.assertEqual(profile['containerInsights']['enabled'], enable)
                self.assertNotEqual(profile['containerInsights'].get('containerNetworkLogs'), 'Enabled')
                if enable:
                    self.assertEqual(profile['containerInsights']['logAnalyticsWorkspaceResourceId'], workspace)
                self.assertTrue(profile['metrics']['enabled'])

    @patch('azure.cli.command_modules.acs.managed_cluster_decorator.ensure_azure_monitor_profile_prerequisites')
    def test_metrics_recovery_update_builds_parent_and_control_plane_profile(self, prerequisites):
        raw = vars(self.parser.parse_args([
            'aks', 'update', '-g', 'rg', '-n', 'cluster',
            '--enable-azure-monitor-metrics', '--enable-control-plane-metrics',
            '--azure-monitor-workspace-resource-id', '/amw',
        ]))
        decorator = AKSManagedClusterUpdateDecorator(
            MockCmd(MockCLI()), Mock(), raw, ResourceType.MGMT_CONTAINERSERVICE
        )
        cluster = models.ManagedCluster(
            location='westus2',
            identity=models.ManagedClusterIdentity(type='SystemAssigned'),
            azure_monitor_profile=models.ManagedClusterAzureMonitorProfile(
                metrics=models.ManagedClusterAzureMonitorProfileMetrics(enabled=False),
            ),
        )
        decorator.context.attach_mc(cluster)
        decorator.context.set_intermediate('subscription_id', 'sub')
        decorator.update_azure_monitor_profile(cluster)
        prerequisites.assert_called_once()
        self.assertEqual(prerequisites.call_args.args[4], 'westus2')
        self.assertEqual(prerequisites.call_args.args[5]['azure_monitor_workspace_resource_id'], '/amw')
        self.assertFalse(prerequisites.call_args.args[6])
        profile = serialize_cluster_request(cluster)['azureMonitorProfile']['metrics']
        self.assertTrue(profile['enabled'])
        self.assertTrue(profile['controlPlane']['enabled'])
