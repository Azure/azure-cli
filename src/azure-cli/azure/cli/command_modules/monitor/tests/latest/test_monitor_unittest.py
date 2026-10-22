# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from unittest import mock

from knack.util import CLIError


def _mock_get_subscription_id(_):
    return '00000000-0000-0000-0000-000000000000'


class MonitorNameOrIdTest(unittest.TestCase):
    def _build_namespace(self, name_or_id=None, resource_group=None, provider_namespace=None, parent=None,
                         resource_type=None):
        from argparse import Namespace
        ns = Namespace()
        ns.name_or_id = name_or_id
        ns.resource_group_name = resource_group
        ns.namespace = provider_namespace
        ns.parent = parent
        ns.resource_type = resource_type
        return ns

    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id', _mock_get_subscription_id)
    def test_monitor_resource_id(self):
        from azure.cli.command_modules.monitor.validators import get_target_resource_validator
        from azure.cli.core.mock import DummyCli

        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        validator = get_target_resource_validator('name_or_id', True)

        id = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/' \
             'virtualMachines/vm1'

        # must supply name or ID
        ns = self._build_namespace()
        with self.assertRaises(CLIError):
            validator(cmd, ns)

        # must only supply ID or name parameters
        ns = self._build_namespace(id, 'my-rg', 'blahblah', 'stuff')
        with self.assertRaises(CLIError):
            validator(cmd, ns)

        # error on invalid ID
        ns = self._build_namespace('bad-id')
        with self.assertRaises(CLIError):
            validator(cmd, ns)

        # allow Provider/Type syntax (same as resource commands)
        ns = self._build_namespace('vm1', 'my-rg', None, None, 'Microsoft.Compute/virtualMachines')
        validator(cmd, ns)
        self.assertEqual(ns.name_or_id, id)

        # allow Provider and Type separate
        ns = self._build_namespace('vm1', 'my-rg', 'Microsoft.Compute', None, 'virtualMachines')
        validator(cmd, ns)
        self.assertEqual(ns.name_or_id, id)

        # verify works with parent
        id = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/' \
             'fakeType/type1/anotherFakeType/type2/virtualMachines/vm1'
        ns = self._build_namespace('vm1', 'my-rg', 'Microsoft.Compute', 'fakeType/type1/anotherFakeType/type2',
                                   'virtualMachines')
        validator(cmd, ns)
        self.assertEqual(ns.name_or_id, id)

        # verify extra parameters are removed
        self.assertFalse(hasattr(ns, 'resource_name'))
        self.assertFalse(hasattr(ns, 'namespace'))
        self.assertFalse(hasattr(ns, 'parent'))
        self.assertFalse(hasattr(ns, 'resource_type'))


class MonitorMetricAlertActionTest(unittest.TestCase):

    def _build_namespace(self, name_or_id=None, resource_group=None, provider_namespace=None, parent=None,
                         resource_type=None):
        from argparse import Namespace
        return Namespace()

    def call_condition(self, ns, value):
        from azure.cli.command_modules.monitor.actions import MetricAlertConditionAction
        MetricAlertConditionAction('--condition', 'condition').__call__(None, ns, value.split(), '--condition')

    def check_condition(self, ns, time_aggregation, metric_namespace, metric_name, operator, threshold, skip_metric_validation):
        prop = ns.condition[0]["static"] if "static" in ns.condition[0] else ns.condition[0]["dynamic"]
        self.assertEqual(prop.get("time_aggregation", None), time_aggregation)
        self.assertEqual(prop.get("metric_name", None), metric_name)
        self.assertEqual(prop.get("operator", None), operator)
        self.assertEqual(prop.get("threshold", None), threshold)
        self.assertEqual(prop.get("metric_namespace", None), metric_namespace)
        self.assertEqual(prop.get("skip_metric_validation", None), skip_metric_validation)

    def check_dimension(self, ns, index, name, operator, values):
        dim = ns.condition[0]["static"]["dimensions"][index] if "static" in ns.condition[0] else ns.condition[0]["dynamic"]["dimensions"][index]
        self.assertEqual(dim.get("name", None), name)
        self.assertEqual(dim.get("operator", None), operator)
        self.assertEqual(dim.get("values", None), values)

    def test_monitor_metric_alert_condition_action(self):

        from knack.util import CLIError

        ns = self._build_namespace()
        self.call_condition(ns, 'avg ns."CPU Percent" > 90')
        self.check_condition(ns, 'Average', 'ns', 'CPU Percent', 'GreaterThan', 90.0, None)

        ns = self._build_namespace()
        self.call_condition(ns, 'avg ns."a.b/c_d" > 90')
        self.check_condition(ns, 'Average', 'ns', 'a.b/c_d', 'GreaterThan', 90.0, None)

        ns = self._build_namespace()
        self.call_condition(ns, 'avg CPU Percent > 90')
        self.check_condition(ns, 'Average', None, 'CPU Percent', 'GreaterThan', 90.0, None)

        ns = self._build_namespace()
        self.call_condition(ns, 'avg "a.b/c_d" > 90')
        self.check_condition(ns, 'Average', None, 'a.b/c_d', 'GreaterThan', 90.0, None)

        ns = self._build_namespace()
        self.call_condition(ns, 'avg SuccessE2ELatency > 250 where ApiName includes GetBlob or PutBlob')
        self.check_condition(ns, 'Average', None, 'SuccessE2ELatency', 'GreaterThan', 250.0, None)
        self.check_dimension(ns, 0, 'ApiName', 'Include', ['GetBlob', 'PutBlob'])

        ns = self._build_namespace()
        self.call_condition(ns, 'avg ns.foo/bar_doo > 90')
        self.check_condition(ns, 'Average', 'ns', 'foo/bar_doo', 'GreaterThan', 90.0, None)

        ns = self._build_namespace()
        with self.assertRaisesRegex(CLIError, 'usage error: --condition'):
            self.call_condition(ns, 'avg blah"what > 90')

        ns = self._build_namespace()
        with self.assertRaisesRegex(CLIError, 'usage error: --condition'):
            self.call_condition(ns, 'avg Wra!!ga * woo')

        ns = self._build_namespace()
        self.call_condition(ns, 'avg SuccessE2ELatenc,|y > 250 where ApiName includes Get|,%_Blob or PutB,_lob')
        self.check_condition(ns, 'Average', None, 'SuccessE2ELatenc,|y', 'GreaterThan', 250.0, None)
        self.check_dimension(ns, 0, 'ApiName', 'Include', ['Get|,%_Blob', 'PutB,_lob'])

        ns = self._build_namespace()
        self.call_condition(ns, 'avg ns.foo/bar_doo > 90 with skipmetricvalidation')
        self.check_condition(ns, 'Average', 'ns', 'foo/bar_doo', 'GreaterThan', 90.0, True)


class MonitorAutoscaleActionTest(unittest.TestCase):

    def _build_namespace(self, name_or_id=None, resource_group=None, provider_namespace=None, parent=None,
                         resource_type=None):
        from argparse import Namespace
        return Namespace()

    def call_condition(self, ns, value):
        from azure.cli.command_modules.monitor.actions import AutoscaleConditionAction
        AutoscaleConditionAction('--condition', 'condition').__call__(None, ns, value.split(), '--condition')

    def check_condition(self, ns, metric_namespace, metric_name, operator, threshold, time_aggregation, time_window):
        prop = ns.condition
        self.assertEqual(prop.time_aggregation, time_aggregation)
        self.assertEqual(prop.metric_namespace, metric_namespace)
        self.assertEqual(prop.metric_name, metric_name)
        self.assertEqual(prop.operator, operator)
        self.assertEqual(prop.threshold, threshold)
        self.assertEqual(prop.time_window, time_window)

    def check_dimension(self, ns, index, dimension_name, operator, values):
        dim = ns.condition.dimensions[index]
        self.assertEqual(dim.dimension_name, dimension_name)
        self.assertEqual(dim.operator, operator)
        self.assertEqual(dim.values, values)

    def test_monitor_autoscale_condition_action(self):

        ns = self._build_namespace()
        self.call_condition(ns, '"ns" CPU Percent > 90 avg 1h5m')
        self.check_condition(ns, 'ns', 'CPU Percent', 'GreaterThan', '90', 'Average', 'PT5M1H')

        ns = self._build_namespace()
        self.call_condition(ns, 'CPU Percent > 90 avg 1h5m')
        self.check_condition(ns, None, 'CPU Percent', 'GreaterThan', '90', 'Average', 'PT5M1H')

        ns = self._build_namespace()
        self.call_condition(ns, 'process.cpu.usage > 0 avg 3m where App == app1 and Deployment == default and Instance == instance1')
        self.check_condition(ns, None, 'process.cpu.usage', 'GreaterThan', '0', 'Average', 'PT3M')
        self.check_dimension(ns, 0, 'App', 'Equals', ['app1'])
        self.check_dimension(ns, 1, 'Deployment', 'Equals', ['default'])
        self.check_dimension(ns, 2, 'Instance', 'Equals', ['instance1'])

        ns = self._build_namespace()
        self.call_condition(ns, '"Microsoft.AppPlatform/Spring" tomcat.global.request.total.count > 0 avg 3m where App == app1 or app3 and Deployment == default and Instance != instance1')
        self.check_condition(ns, "Microsoft.AppPlatform/Spring", 'tomcat.global.request.total.count', 'GreaterThan', '0', 'Average', 'PT3M')
        self.check_dimension(ns, 0, 'App', 'Equals', ['app1', 'app3'])
        self.check_dimension(ns, 1, 'Deployment', 'Equals', ['default'])
        self.check_dimension(ns, 2, 'Instance', 'NotEquals', ['instance1'])

        ns = self._build_namespace()
        self.call_condition(ns, '"kubernetes custom metrics %#*@_-" tomcat.global.request.total.count > 0 avg 3m where App == app1 or app3 and Deployment == default and Instance != instance1')
        self.check_condition(ns, "kubernetes custom metrics %#*@_-", 'tomcat.global.request.total.count', 'GreaterThan',
                             '0', 'Average', 'PT3M')
        self.check_dimension(ns, 0, 'App', 'Equals', ['app1', 'app3'])
        self.check_dimension(ns, 1, 'Deployment', 'Equals', ['default'])
        self.check_dimension(ns, 2, 'Instance', 'NotEquals', ['instance1'])


class MonitorTraceTest(unittest.TestCase):
    subscription = '00000000-0000-0000-0000-000000000000'

    def test_monitor_trace_association_scope(self):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        from azure.cli.command_modules.monitor.operations.trace_association import _Scope

        scope = _Scope('/subscriptions/{}/'.format(self.subscription))
        self.assertEqual((scope.kind, scope.args), ('subscription', {'subscription': self.subscription}))

        scope = _Scope('/subscriptions/{}/resourceGroups/rg1'.format(self.subscription))
        self.assertEqual((scope.kind, scope.args),
                         ('resource_group', {'subscription': self.subscription, 'resource_group': 'rg1'}))

        scope = _Scope('/SUBSCRIPTIONS/{}/resourcegroups/rg1/providers/microsoft.insights/components/ai1'.format(
            self.subscription))
        self.assertEqual(scope.kind, 'resource')
        self.assertEqual(scope.id, '/subscriptions/{}/resourceGroups/rg1/providers/Microsoft.Insights/components/ai1'
                         .format(self.subscription))
        self.assertEqual(scope.args, {'subscription': self.subscription, 'resource_group': 'rg1',
                                      'provider_name': 'Microsoft.Insights', 'provider_type': 'components',
                                      'resource_name': 'ai1'})

        for resource_uri in ('rg1', '/subscriptions/mysubscription',
                             '/subscriptions/{}/resourceGroups/rg1/providers/Microsoft.Web/sites/app1'.format(
                                 self.subscription)):
            with self.assertRaises(InvalidArgumentValueError):
                _Scope(resource_uri)

    def test_monitor_trace_workspace_id(self):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        from azure.cli.command_modules.monitor.operations.trace_container import parse_workspace_id

        workspace_id = '/subscriptions/{}/resourceGroups/rg1/providers/Microsoft.Monitor/accounts/amw1'.format(
            self.subscription)
        self.assertEqual(parse_workspace_id(workspace_id), {
            'subscription': self.subscription, 'resource_group': 'rg1', 'azure_monitor_workspace_name': 'amw1'})
        for bad_id in ('amw1', workspace_id + '/traceContainers/default',
                       workspace_id.replace('Microsoft.Monitor/accounts', 'Microsoft.OperationalInsights/workspaces')):
            with self.assertRaises(InvalidArgumentValueError):
                parse_workspace_id(bad_id)

    def test_monitor_trace_container_settings(self):
        from azure.cli.command_modules.monitor.operations.trace_container import trace_container_settings

        # A container created before retention existed reports no retention and keeps the default.
        settings = trace_container_settings({'properties': {'traceDurationWindowInSeconds': 300,
                                                            'traceMetricsState': 'Disabled'}})
        self.assertEqual(settings, {'retention_days': 30, 'trace_duration_window': 300, 'trace_metrics': 'Disabled'})
