# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime as dt
import importlib
import unittest
from urllib.parse import parse_qs, unquote, urlsplit
from unittest import mock


CUSTOM_IMPLEMENTATIONS = (
    (
        'azure.cli.command_modules.monitor.custom',
        'azure.cli.command_modules.monitor.aaz.latest.monitor.activity_log._list.List',
        'azure.cli.command_modules.monitor.aaz.latest.monitor.metrics._list.List',
    ),
    (
        'azure.cli.command_modules.monitor._legacy.custom',
        'azure.cli.command_modules.monitor._legacy.aaz.latest.monitor.activity_log.List',
        'azure.cli.command_modules.monitor._legacy.aaz.latest.monitor.metrics.List',
    ),
)


class MonitorCustomTimeDefaultsTest(unittest.TestCase):

    def _capture_command_args(self, list_class_path, command, **kwargs):
        cmd = mock.Mock()
        with mock.patch(list_class_path) as list_class:
            list_class.return_value.return_value = []
            result = command(cmd, **kwargs)

        self.assertEqual(result, [])
        list_class.assert_called_once_with(cli_ctx=cmd.cli_ctx)
        return list_class.return_value.call_args.kwargs['command_args']

    def test_activity_log_default_window_is_aware_utc(self):
        fixed_now = dt.datetime(2026, 11, 1, 12, 30, 45, 123456, tzinfo=dt.UTC)
        expected_filter = (
            'eventTimestamp ge 2026-11-01T06:30:45.123456+00:00 '
            'and eventTimestamp le 2026-11-01T12:30:45.123456+00:00'
        )

        for module_path, activity_log_list_path, _ in CUSTOM_IMPLEMENTATIONS:
            with self.subTest(implementation=module_path):
                module = importlib.import_module(module_path)
                with mock.patch('datetime.datetime', wraps=dt.datetime) as mock_datetime:
                    mock_datetime.now.return_value = fixed_now
                    command_args = self._capture_command_args(
                        activity_log_list_path,
                        module.list_activity_log,
                        offset=dt.timedelta(hours=6),
                    )

                mock_datetime.now.assert_has_calls([mock.call(dt.UTC)])
                self.assertEqual(command_args['filter'], expected_filter)

    def test_metrics_default_timespan_is_aware_utc_and_keeps_interval(self):
        fixed_now = dt.datetime(2026, 11, 1, 12, 30, 45, 123456, tzinfo=dt.UTC)
        expected_timespan = (
            '2026-11-01T11%3A30%3A45.123456%2B00%3A00'
            '%2F2026-11-01T12%3A30%3A45.123456%2B00%3A00'
        )

        for module_path, _, metrics_list_path in CUSTOM_IMPLEMENTATIONS:
            with self.subTest(implementation=module_path):
                module = importlib.import_module(module_path)
                with mock.patch('datetime.datetime', wraps=dt.datetime) as mock_datetime:
                    mock_datetime.now.return_value = fixed_now
                    command_args = self._capture_command_args(
                        metrics_list_path,
                        module.list_metrics,
                        resource='/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Test/items/item',
                        offset=dt.timedelta(hours=1),
                    )

                mock_datetime.now.assert_has_calls([mock.call(dt.UTC)])
                self.assertEqual(command_args['timespan'], expected_timespan)
                self.assertEqual(command_args['interval'], '1m')

    def test_explicit_time_bounds_are_passed_through(self):
        start_time = '2026-10-31T21:45:00-04:00'
        end_time = '2026-11-01T09:15:00+05:30'

        for module_path, activity_log_list_path, metrics_list_path in CUSTOM_IMPLEMENTATIONS:
            with self.subTest(implementation=module_path):
                module = importlib.import_module(module_path)
                activity_log_args = self._capture_command_args(
                    activity_log_list_path,
                    module.list_activity_log,
                    start_time=start_time,
                    end_time=end_time,
                    offset=dt.timedelta(hours=6),
                )
                metrics_args = self._capture_command_args(
                    metrics_list_path,
                    module.list_metrics,
                    resource='/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Test/items/item',
                    start_time=start_time,
                    end_time=end_time,
                    interval='5m',
                    offset=dt.timedelta(hours=1),
                )

                self.assertEqual(
                    activity_log_args['filter'],
                    f'eventTimestamp ge {start_time} and eventTimestamp le {end_time}',
                )
                self.assertEqual(
                    metrics_args['timespan'],
                    '2026-10-31T21%3A45%3A00-04%3A00%2F2026-11-01T09%3A15%3A00%2B05%3A30',
                )
                self.assertEqual(metrics_args['interval'], '5m')

    def test_default_utc_windows_reach_serialized_aaz_requests(self):
        from azure.cli.core.aaz._client import AAZBaseClient
        from azure.cli.core.aaz._command_ctx import AAZCommandCtx
        from azure.cli.core.mock import DummyCli
        from azure.core.pipeline.policies import ContentDecodePolicy

        fixed_now = dt.datetime(2026, 11, 1, 12, 30, 45, 123456, tzinfo=dt.UTC)
        expected_activity_filter = (
            'eventTimestamp ge 2026-11-01T06:30:45.123456+00:00 '
            'and eventTimestamp le 2026-11-01T12:30:45.123456+00:00'
        )
        expected_timespan = (
            '2026-11-01T11:30:45.123456+00:00/2026-11-01T12:30:45.123456+00:00'
        )
        requests = []
        cli_ctx = DummyCli()
        cli_ctx.cloud = mock.Mock()
        cli_ctx.cloud.endpoints.resource_manager = 'https://management.azure.com/'
        cli_ctx.cloud.endpoints.active_directory = 'https://login.microsoftonline.com/'
        cli_ctx.cloud.endpoints.active_directory_resource_id = 'https://management.core.windows.net/'
        cli_ctx.data['subscription_id'] = 'sub'
        cmd = mock.Mock(cli_ctx=cli_ctx)

        def send_request(_client, request, **kwargs):
            requests.append(request)
            if '/metrics' in urlsplit(request.url).path:
                payload = {'timespan': expected_timespan, 'value': []}
            else:
                payload = {'value': [{'eventTimestamp': fixed_now.isoformat()}]}

            session = mock.Mock()
            session.http_response.status_code = 200
            session.context = {ContentDecodePolicy.CONTEXT_NAME: payload}
            return session

        with mock.patch.object(AAZCommandCtx, 'get_login_credential', return_value=mock.Mock()), \
                mock.patch.object(AAZBaseClient, 'send_request', new=send_request), \
                mock.patch('datetime.datetime', wraps=dt.datetime) as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            for module_path, _, _ in CUSTOM_IMPLEMENTATIONS:
                with self.subTest(implementation=module_path):
                    module = importlib.import_module(module_path)
                    activity_log = module.list_activity_log(
                        cmd,
                        offset=dt.timedelta(hours=6),
                    )
                    metrics = module.list_metrics(
                        cmd,
                        resource='/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Test/items/item',
                        offset=dt.timedelta(hours=1),
                    )

                    self.assertEqual(activity_log[0]['eventTimestamp'], fixed_now.isoformat())
                    self.assertEqual(metrics['timespan'], expected_timespan)

                    activity_request, metrics_request = requests[-2:]
                    self.assertEqual(activity_request.method, 'GET')
                    self.assertEqual(urlsplit(activity_request.url).netloc, 'management.azure.com')
                    self.assertEqual(
                        urlsplit(activity_request.url).path,
                        '/subscriptions/sub/providers/Microsoft.Insights/eventtypes/management/values',
                    )
                    self.assertEqual(
                        parse_qs(urlsplit(activity_request.url).query)['$filter'],
                        [expected_activity_filter],
                    )

                    metrics_query = parse_qs(urlsplit(metrics_request.url).query)
                    self.assertEqual(urlsplit(metrics_request.url).netloc, 'management.azure.com')
                    self.assertEqual(
                        urlsplit(metrics_request.url).path,
                        '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Test/items/item'
                        '/providers/Microsoft.Insights/metrics',
                    )
                    self.assertEqual(metrics_query['interval'], ['PT1M'])
                    self.assertIn('%252B00%253A00%252F', urlsplit(metrics_request.url).query)
                    self.assertEqual(unquote(metrics_query['timespan'][0]), expected_timespan)
