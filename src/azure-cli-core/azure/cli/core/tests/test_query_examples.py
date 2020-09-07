# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import json

from azure.cli.core.commands.query_examples import TreeBuilder
from azure.cli.core.commands.query_examples import TreeNode


class MockConfig:
    def __init__(self):
        self._config = {
            'examples_len': '80',
            'help_len': '80',
            'max_examples': '-1'
        }

    def get(self, module, field, default_value):
        if module != 'query':
            return default_value
        return self._config.get(field, default_value)


class TestQueryExamplesTreeBuilder(unittest.TestCase):
    def examples_to_dict(self, examples):
        ans = {}
        for ex in examples:
            ans[ex['query string']] = ex
        return ans

    def test_do_parse_dict(self):
        input_json = '''
        {
            "name": {
                "firstName": "Ann",
                "lastName": "Bnn"
            }
        }
        '''
        json_obj = json.loads(input_json)
        mock_config = MockConfig()
        builder = TreeBuilder(mock_config)
        builder.build(json_obj)
        self.assertIsNotNone(builder._root)
        self.assertIsNotNone(builder._all_nodes)
        self.assertIsInstance(builder._all_nodes, dict)
        self.assertIn('name', builder._all_nodes)
        self.assertIn('firstName', builder._all_nodes)
        self.assertIn('lastName', builder._all_nodes)

    def test_do_parse_list(self):
        input_json = '''
        [{
            "name": {
                "firstName": "Ann",
                "lastName": "Bnn"
            }
        }]
        '''
        json_obj = json.loads(input_json)
        mock_config = MockConfig()
        builder = TreeBuilder(mock_config)
        builder.build(json_obj)
        self.assertIsNotNone(builder._root)
        self.assertIsNotNone(builder._all_nodes)
        self.assertIsInstance(builder._all_nodes, dict)
        self.assertIn('name', builder._all_nodes)
        self.assertIn('firstName', builder._all_nodes)
        self.assertIn('lastName', builder._all_nodes)
        # check list
        self.assertTrue(builder._root._under_array)

    def test_parse_empty(self):
        mock_config = MockConfig()
        empty_dict = '{}'
        json_obj = json.loads(empty_dict)
        builder = TreeBuilder(mock_config)
        builder.build(json_obj)
        self.assertIsNotNone(builder._root)  # an empty node
        self.assertFalse(builder._root._child)

        empty_list = '[]'
        json_obj = json.loads(empty_list)
        builder = TreeBuilder(mock_config)
        builder.build(json_obj)
        self.assertIsNone(builder._root)  # No node found

        empty_list = '[{},{}]'
        json_obj = json.loads(empty_list)
        builder = TreeBuilder(mock_config)
        builder.build(json_obj)
        self.assertIsNotNone(builder._root)  # an empty node
        self.assertFalse(builder._root._child)

    def test_dict_recommend(self):
        mock_config = MockConfig()
        keyword_list = []
        output_format = 'json'

        input_json = '''
        {
            "name": {
                "firstName": "Ann"
            },
            "age": 20
        }
        '''
        json_obj = json.loads(input_json)
        builder = TreeBuilder(mock_config)
        builder.build(json_obj)
        examples_list = builder.generate_examples(keyword_list, output_format)
        examples = self.examples_to_dict(examples_list)
        self.assertIn('name', examples)
        self.assertIn('name.firstName', examples)
        self.assertIn('age', examples)

    def test_array_recommend(self):
        mock_config = MockConfig()
        keyword_list = []
        output_format = 'json'

        input_json = '''
        [{
            "name": {
                "firstName": "Ann"
            },
            "age": "20",
            "friends": [
                {
                    "Name": "Bob"
                }
            ]
        }]
        '''
        json_obj = json.loads(input_json)
        builder = TreeBuilder(mock_config)
        builder.build(json_obj)
        examples_list = builder.generate_examples(keyword_list, output_format)
        examples = self.examples_to_dict(examples_list)
        self.assertIn('[].name', examples)
        self.assertIn('[].name.firstName', examples)
        self.assertIn("[?name.firstName=='Ann']", examples)
        self.assertIn('[].age', examples)
        self.assertIn("[?age=='20']", examples)
        self.assertIn('[].friends[].Name', examples)
        self.assertIn("[].friends[?Name=='Bob']", examples)


if __name__ == "__main__":
    unittest.main()
