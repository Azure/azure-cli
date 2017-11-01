# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock
import re
from knack.util import CLIError
from azure.cli.command_modules.monitor.custom import (_metric_names_filter_builder,
                                                      _metrics_odata_filter_builder,
                                                      _build_activity_log_odata_filter,
                                                      _activity_log_select_filter_builder,
                                                      _build_odata_filter,
                                                      scaffold_autoscale_settings_parameters)


class FilterBuilderTests(unittest.TestCase):

    def test_metric_names_filter_builder(self):
        metric_names = None
        filter_output = _metric_names_filter_builder(metric_names)
        assert filter_output == ''

        metric_names = ['ActionsCompleted']
        filter_output = _metric_names_filter_builder(metric_names)
        assert filter_output == "name.value eq '{}'".format(metric_names[0])

        metric_names = ['RunsSucceeded', 'ActionsCompleted']
        filter_output = _metric_names_filter_builder(metric_names)
        assert filter_output == 'name.value eq \'{}\' or name.value eq \'{}\''.format(
            metric_names[0], metric_names[1])

    def test_metrics_odata_filter_builder(self):
        filter_output = _metrics_odata_filter_builder('PT1M')
        regex = r'^(timeGrain eq duration).*(startTime eq).*(endTime eq).*$'
        assert bool(re.search(regex, filter_output))

        filter_output = _metrics_odata_filter_builder('PT1M', '1970-01-01T00:00:00Z')
        assert bool(re.search(regex, filter_output))

        filter_output = _metrics_odata_filter_builder('PT1M', end_time='1970-01-01T00:00:00Z')
        assert bool(re.search(regex, filter_output))

        metric_names = ['ActionsCompleted']
        regex = r'^(\(name.value eq).*(timeGrain eq duration).*(startTime eq).*(endTime eq).*$'
        filter_output = _metrics_odata_filter_builder('PT1M', metric_names=metric_names)
        assert bool(re.search(regex, filter_output))

    def test_build_activity_logs_odata_filter(self):
        correlation_id = '1234-34567-56789-34567'
        resource_group = 'test'
        resource_id = '/subscriptions/xxxx-xxxx-xxxx-xxx/resourceGroups/testrg/providers/' \
                      'Microsoft.Web/sites/testwebapp'
        resource_provider = 'Microsoft.Web'
        caller = 'contoso@contoso.com'
        status = 'RunsSucceeded'

        filter_output = _build_activity_log_odata_filter(correlation_id)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(correlationId eq).*$'
        assert bool(re.search(regex, filter_output))

        filter_output = _build_activity_log_odata_filter(resource_group=resource_group)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(resourceGroupName eq).*$'
        assert bool(re.search(regex, filter_output))

        filter_output = _build_activity_log_odata_filter(resource_id=resource_id)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(resourceId eq).*$'
        assert bool(re.search(regex, filter_output))

        filter_output = _build_activity_log_odata_filter(resource_provider=resource_provider)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(resourceProvider eq).*$'
        assert bool(re.search(regex, filter_output))

        filter_output = _build_activity_log_odata_filter(caller=caller)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(caller eq).*$'
        assert bool(re.search(regex, filter_output))

        filter_output = _build_activity_log_odata_filter(status=status)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(status eq).*$'
        assert bool(re.search(regex, filter_output))

    def test_activity_logs_select_filter_builder(self):
        select_output = _activity_log_select_filter_builder()
        assert select_output is None

        events = ['channels']
        select_output = _activity_log_select_filter_builder(events)
        assert select_output == '{}'.format(events[0])

        events = ['eventDataId', 'eventSource']
        select_output = _activity_log_select_filter_builder(events)
        assert select_output == '{} , {}'.format(events[0], events[1])

    def test_build_odata_filter(self):
        default_filter = "timeGrain eq duration'PT1M'"
        field_name = 'correlation_id'
        field_value = '1234-34567-56789-34567'
        field_label = 'correlationId'

        filter_output = _build_odata_filter(default_filter, field_name, field_value, field_label)
        regex = r'^({} and {} eq \'{}\')$'.format(default_filter, field_label, field_value)
        assert bool(re.search(regex, filter_output))

        with self.assertRaises(CLIError):
            _build_odata_filter(default_filter, field_name, None, field_label)

    def test_scaffold_autoscale_settings_parameters(self):
        template = scaffold_autoscale_settings_parameters(None)
        if not template or not isinstance(template, dict):
            assert False


def _mock_get_subscription_id():
    return '00000000-0000-0000-0000-000000000000'


class MonitorNameOrIdTest(unittest.TestCase):

    def _build_namespace(self, name_or_id=None, resource_group=None, provider_namespace=None, parent=None, resource_type=None):
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
        validator = get_target_resource_validator('name_or_id', True)

        id = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/vm1'

        # must supply name or ID
        ns = self._build_namespace()
        with self.assertRaises(CLIError):
            validator(ns)

        # must only supply ID or name parameters
        ns = self._build_namespace(id, 'my-rg', 'blahblah', 'stuff')
        with self.assertRaises(CLIError):
            validator(ns)

        # error on invalid ID
        ns = self._build_namespace('bad-id')
        with self.assertRaises(CLIError):
            validator(ns)

        # allow Provider/Type syntax (same as resource commands)
        ns = self._build_namespace('vm1', 'my-rg', None, None, 'Microsoft.Compute/virtualMachines')
        validator(ns)
        self.assertEqual(ns.name_or_id, id)

        # allow Provider and Type separate
        ns = self._build_namespace('vm1', 'my-rg', 'Microsoft.Compute', None, 'virtualMachines')
        validator(ns)
        self.assertEqual(ns.name_or_id, id)

        # verify works with parent
        id = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/fakeType/type1/anotherFakeType/type2/virtualMachines/vm1'
        ns = self._build_namespace('vm1', 'my-rg', 'Microsoft.Compute', 'fakeType/type1/anotherFakeType/type2', 'virtualMachines')
        validator(ns)
        self.assertEqual(ns.name_or_id, id)

        # verify extra parameters are removed
        self.assertFalse(hasattr(ns, 'resource_name'))
        self.assertFalse(hasattr(ns, 'namespace'))
        self.assertFalse(hasattr(ns, 'parent'))
        self.assertFalse(hasattr(ns, 'resource_type'))
