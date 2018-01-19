# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import re

from knack.util import CLIError

from azure.cli.command_modules.monitor.operations.activity_log import (_build_activity_log_odata_filter,
                                                                       _activity_log_select_filter_builder,
                                                                       _build_odata_filter)


class TestActivityLogODataBuilderComponents(unittest.TestCase):
    def test_build_activity_logs_odata_filter(self):
        correlation_id = '1234-34567-56789-34567'
        resource_group = 'test'
        resource_id = '/subscriptions/xxxx-xxxx-xxxx-xxx/resourceGroups/testrg/providers/Microsoft.Web/sites/testwebapp'
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
