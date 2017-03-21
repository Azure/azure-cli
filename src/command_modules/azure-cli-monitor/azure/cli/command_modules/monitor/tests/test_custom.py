# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import re
from azure.cli.core._util import CLIError
from azure.cli.command_modules.monitor.custom import (_metric_names_filter_builder,
                                                      _metrics_odata_filter_builder,
                                                      _build_activity_logs_odata_filter,
                                                      _activity_logs_select_filter_builder,
                                                      _build_odata_filter,
                                                      scaffold_autoscale_settings_parameters)


class CustomCommandTest(unittest.TestCase):
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

        filter_output = _build_activity_logs_odata_filter(correlation_id)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(correlationId eq).*$'
        assert bool(re.search(regex, filter_output))

        filter_output = _build_activity_logs_odata_filter(resource_group=resource_group)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(resourceGroupName eq).*$'
        assert bool(re.search(regex, filter_output))

        filter_output = _build_activity_logs_odata_filter(resource_id=resource_id)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(resourceId eq).*$'
        assert bool(re.search(regex, filter_output))

        filter_output = _build_activity_logs_odata_filter(resource_provider=resource_provider)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(resourceProvider eq).*$'
        assert bool(re.search(regex, filter_output))

        filter_output = _build_activity_logs_odata_filter(caller=caller)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(caller eq).*$'
        assert bool(re.search(regex, filter_output))

        filter_output = _build_activity_logs_odata_filter(status=status)
        regex = r'^(eventTimestamp ge).*(eventTimestamp le).*(status eq).*$'
        assert bool(re.search(regex, filter_output))

    def test_activity_logs_select_filter_builder(self):
        select_output = _activity_logs_select_filter_builder()
        assert select_output is None

        events = ['channels']
        select_output = _activity_logs_select_filter_builder(events)
        assert select_output == '{}'.format(events[0])

        events = ['eventDataId', 'eventSource']
        select_output = _activity_logs_select_filter_builder(events)
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
