# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from unittest import mock
import requests

from azure.cli.command_modules.find.custom import (Example, call_aladdin_service,
                                                   get_generated_examples, clean_from_http_answer)


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


if __name__ == '__main__':
    unittest.main()
