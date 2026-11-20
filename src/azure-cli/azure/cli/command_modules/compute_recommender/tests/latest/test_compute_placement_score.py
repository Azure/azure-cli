# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import io
import json
import shlex
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from azure.core.exceptions import HttpResponseError
from azure.core.pipeline.policies import ContentDecodePolicy
from azure.cli.core import get_default_cli
from azure.cli.core.aaz import AAZCommand
from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import RecordingProcessor
from azure.cli.command_modules.compute_recommender.aaz.latest.compute_recommender import ComputePlacementScore


SUBSCRIPTION = '00000000-0000-0000-0000-000000000000'


class ComputePlacementScoreTest(unittest.TestCase):

    def setUp(self):
        self.cli_ctx = get_default_cli()

    def _operation(self, **kwargs):
        command = ComputePlacementScore(cli_ctx=self.cli_ctx)
        args = {
            'location': 'eastus',
            'desired_sizes': [{'sku': 'Standard_D2_v2'}],
            'subscription': SUBSCRIPTION,
        }
        args.update(kwargs)
        AAZCommand._handler(command, args)
        with patch.object(command.ctx, 'get_login_credential', return_value=Mock()):
            operation = command.ComputePlacementScoresPost(command.ctx)
        self.addCleanup(operation.client.close)
        return command, operation

    def test_minimal_request_omits_service_defaults(self):
        _, operation = self._operation()
        request = operation.make_request()
        self.assertEqual('POST', request.method)
        self.assertEqual(
            '/subscriptions/' + SUBSCRIPTION +
            '/providers/Microsoft.Compute/locations/eastus/placementScores/regular/generate',
            urlparse(request.url).path,
        )
        self.assertEqual({'api-version': ['2026-10-05-preview']}, parse_qs(urlparse(request.url).query))
        self.assertEqual({'desiredSizes': [{'sku': 'Standard_D2_v2'}]}, json.loads(request.body))

    def test_request_preserves_explicit_false_and_zero(self):
        _, operation = self._operation(
            availability_zones=False,
            desired_count=0,
            desired_locations=['eastus', 'eastus2'],
            desired_sizes=[{'sku': 'Standard_D2_v2'}, {'sku': 'Standard_D4_v2'}],
        )
        self.assertEqual({
            'availabilityZones': False,
            'desiredCount': 0,
            'desiredLocations': ['eastus', 'eastus2'],
            'desiredSizes': [{'sku': 'Standard_D2_v2'}, {'sku': 'Standard_D4_v2'}],
        }, json.loads(operation.make_request().body))

    def test_response_preserves_placement_preferences_and_scores(self):
        command, operation = self._operation()
        data = {
            'availabilityZones': True,
            'desiredCount': 1,
            'desiredLocations': ['eastus', 'eastus2'],
            'desiredSizes': [{'sku': 'Standard_D2_v2'}],
            'placementScores': [
                {'availabilityZone': '1', 'placementPreference': 10, 'region': 'eastus',
                 'score': 'High', 'sku': 'Standard_D2_v2'},
                {'availabilityZone': '2', 'placementPreference': 0, 'region': 'eastus2',
                 'score': 'DataNotFoundOrStale', 'sku': 'Standard_D2_v2'},
            ],
        }
        session = SimpleNamespace(
            http_response=SimpleNamespace(status_code=200),
            context={ContentDecodePolicy.CONTEXT_NAME: data},
        )
        with patch.object(operation.client, 'send_request', return_value=session):
            operation()
        self.assertEqual(data, command._output())

    def test_service_errors_are_not_swallowed(self):
        _, operation = self._operation()
        response = Mock(status_code=400, reason='Bad Request', headers={})
        response.text.return_value = json.dumps({'error': {'code': 'InvalidRequest', 'message': 'Invalid SKU.'}})
        with patch.object(operation.client, 'send_request',
                          return_value=SimpleNamespace(http_response=response)):
            with self.assertRaises(HttpResponseError):
                operation()

    def test_help_examples_parse_and_required_sizes_are_enforced(self):
        examples = [line.strip() for line in ComputePlacementScore.__doc__.splitlines()
                    if line.strip().startswith('az ')]
        cases = [(shlex.split(example)[1:], 0) for example in examples]
        cases.append((['compute-recommender', 'compute-placement-score', '--location', 'eastus'], 2))
        for args, expected in cases:
            with self.subTest(args=args):
                parsed = []

                def capture(command, command_args):
                    AAZCommand._handler(command, command_args)
                    parsed.append(command.ctx.args)

                output = io.StringIO()
                with patch.object(ComputePlacementScore, '_handler', capture), \
                        contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    try:
                        result = self.cli_ctx.invoke(args + ['--subscription', SUBSCRIPTION], out_file=output)
                    except SystemExit as error:
                        result = error.code
                self.assertEqual(expected, result, output.getvalue())
                self.assertEqual(expected == 0, bool(parsed))

    def test_scenario_commands_format_literal_sku_braces(self):
        for method in ('test_compute_placement_score_generate',
                       'test_compute_placement_score_generate_without_desired_locations'):
            with self.subTest(method=method):
                scenario = ComputePlacementScoreScenario(method)
                data = {
                    'desiredLocations': ['eastus'],
                    'desiredCount': 1,
                    'placementScores': [{
                        'region': 'eastus', 'sku': 'Standard_D2_v2', 'placementPreference': 10,
                    }],
                }
                commands = []

                def capture(command):
                    commands.append(scenario._apply_kwargs(command))
                    return SimpleNamespace(get_output_in_json=lambda: data)

                with patch.object(scenario, 'get_subscription_id', return_value=SUBSCRIPTION), \
                        patch.object(scenario, 'cmd', side_effect=capture):
                    getattr(scenario, method)()
                self.assertEqual(1, len(commands))
                self.assertIn('{sku:Standard_D2_v2}', commands[0])


class _ComputePlacementScoreRecordingProcessor(RecordingProcessor):
    def process_response(self, response):
        self.replace_header_fn(response, 'x-ms-operation-identifier', lambda _: 'redacted')
        return response


class ComputePlacementScoreScenario(ScenarioTest):
    def __init__(self, method_name):
        super().__init__(method_name, recording_processors=[_ComputePlacementScoreRecordingProcessor()])

    def test_compute_placement_score_generate(self):
        self.kwargs['subscription'] = self.get_subscription_id()
        result = self.cmd(
            'az compute-recommender compute-placement-score --location eastus '
            '--subscription {subscription} --availability-zones true '
            '--desired-locations eastus eastus2 --desired-count 10 '
            '--desired-sizes "[{{sku:Standard_D2_v2}},{{sku:Standard_D4_v2}}]"'
        ).get_output_in_json()
        self.assertTrue(result['placementScores'])
        for score in result['placementScores']:
            self.assertIn(score['region'], ['eastus', 'eastus2'])
            self.assertIn(score['sku'], ['Standard_D2_v2', 'Standard_D4_v2'])
            self.assertGreaterEqual(score['placementPreference'], 0)
            self.assertLessEqual(score['placementPreference'], 10)

    def test_compute_placement_score_generate_without_desired_locations(self):
        result = self.cmd(
            'az compute-recommender compute-placement-score --location eastus '
            '--desired-sizes "[{{sku:Standard_D2_v2}}]"'
        ).get_output_in_json()
        self.assertEqual(['eastus'], result['desiredLocations'])
        self.assertEqual(1, result['desiredCount'])
        self.assertTrue(result['placementScores'])
