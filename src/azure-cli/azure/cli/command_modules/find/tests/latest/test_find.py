# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import unittest
from unittest import mock
import requests

from azure.cli.command_modules.find.custom import (Example, call_aladdin_service,
                                                   get_generated_examples, clean_from_http_answer,
                                                   process_query, _filter_existing_command_examples)


def create_valid_http_response():
    mock_response = requests.Response()
    mock_response.status_code = 200
    data = [{
        'title': 'RunTestAutomation',
        'snippet': 'az find'
    }, {
        'title': 'az test',
        'snippet': 'The title'
    }]
    mock_response._content = json.dumps(data)
    return mock_response


def create_empty_http_response():
    mock_response = requests.Response()
    mock_response.status_code = 200
    data = []
    mock_response._content = json.dumps(data)
    return mock_response


def create_response_with_stale_command():
    mock_response = requests.Response()
    mock_response.status_code = 200
    data = [{
        'title': 'Get the details of a CDN WAF policy.',
        'snippet': 'az cdn waf policy show --resource-group group --name policy'
    }, {
        'title': 'Get the details of a Front Door WAF policy.',
        'snippet': 'az network front-door waf-policy show --resource-group group --name policy'
    }]
    mock_response._content = json.dumps(data)
    return mock_response


class FindCustomCommandTest(unittest.TestCase):

    def test_call_aladdin_service(self):
        mock_response = create_valid_http_response()

        with mock.patch('requests.get', return_value=(mock_response)):
            response = call_aladdin_service('RunTestAutomation')
            self.assertEqual(200, response.status_code)
            self.assertEqual(2, len(json.loads(response.content)))

    def test_example_clean_from_http_answer(self):
        cleaned_responses = []
        mock_response = create_valid_http_response()

        for response in json.loads(mock_response.content):
            cleaned_responses.append(clean_from_http_answer(response))

        self.assertEqual('RunTestAutomation', cleaned_responses[0].title)
        self.assertEqual('az find', cleaned_responses[0].snippet)
        self.assertEqual('The title', cleaned_responses[1].title)
        self.assertEqual('az test', cleaned_responses[1].snippet)

    def test_get_generated_examples_full(self):
        examples = []
        mock_response = create_valid_http_response()

        with mock.patch('requests.get', return_value=(mock_response)):
            examples = get_generated_examples('RunTestAutomation')

            self.assertEqual('RunTestAutomation', examples[0].title)
            self.assertEqual('az find', examples[0].snippet)
            self.assertEqual('The title', examples[1].title)
            self.assertEqual('az test', examples[1].snippet)

    def test_get_generated_examples_empty(self):
        examples = []
        mock_response = create_empty_http_response()

        with mock.patch('requests.get', return_value=(mock_response)):
            examples = get_generated_examples('RunTestAutomation')

            self.assertEqual(0, len(examples))

    def test_filter_existing_command_examples(self):
        mock_response = create_response_with_stale_command()
        command_loader = mock.Mock()

        def load_command_table(args):
            command_name = ' '.join(args)
            command_loader.command_table = {
                command_name: mock.Mock()
            } if command_name == 'network front-door waf-policy show' else {}

        command_loader.load_command_table.side_effect = load_command_table

        examples = _filter_existing_command_examples(json.loads(mock_response.content), command_loader)

        self.assertEqual(1, len(examples))
        self.assertEqual('Get the details of a Front Door WAF policy.', examples[0]['title'])

    def test_process_query_filters_stale_examples(self):
        mock_response = create_response_with_stale_command()
        command_loader = mock.Mock()

        def load_command_table(args):
            command_name = ' '.join(args)
            command_loader.command_table = {
                command_name: mock.Mock()
            } if command_name == 'network front-door waf-policy show' else {}

        command_loader.load_command_table.side_effect = load_command_table
        cmd = mock.Mock()
        cmd.cli_ctx.invocation.commands_loader = command_loader
        stdout = StringIO()
        stderr = StringIO()

        with mock.patch('requests.get', return_value=mock_response), \
                mock.patch('azure.cli.core.util.show_updates_available'), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            process_query(cmd, 'waf')

        self.assertNotIn('az cdn waf policy show', stdout.getvalue())
        self.assertIn('az network front-door waf-policy show', stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
