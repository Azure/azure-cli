# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import json

from azure.cli.core.commands.query_examples import QueryTreeBuilder
from azure.cli.core.commands.query_examples import QueryExample


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

    def set(self, field, value):
        if field in self._config:
            self._config[field] = value


class TestQueryExamplesQueryTreeBuilder(unittest.TestCase):
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
        builder = QueryTreeBuilder(mock_config)
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
        builder = QueryTreeBuilder(mock_config)
        builder.build(json_obj)
        self.assertIsNotNone(builder._root)
        self.assertIsNotNone(builder._all_nodes)
        self.assertIsInstance(builder._all_nodes, dict)
        self.assertIn('name', builder._all_nodes)
        self.assertIn('firstName', builder._all_nodes)
        self.assertIn('lastName', builder._all_nodes)
        # check list
        self.assertTrue(builder._root._is_array)

    def test_parse_empty(self):
        mock_config = MockConfig()
        empty_dict = '{}'
        json_obj = json.loads(empty_dict)
        builder = QueryTreeBuilder(mock_config)
        builder.build(json_obj)
        self.assertIsNotNone(builder._root)  # an empty node
        self.assertFalse(builder._root._child)

        empty_list = '[]'
        json_obj = json.loads(empty_list)
        builder = QueryTreeBuilder(mock_config)
        builder.build(json_obj)
        self.assertIsNone(builder._root)  # No node found

        empty_list = '[{},{}]'
        json_obj = json.loads(empty_list)
        builder = QueryTreeBuilder(mock_config)
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
        builder = QueryTreeBuilder(mock_config)
        builder.build(json_obj)
        examples_list = builder.generate_examples(keyword_list, output_format)
        examples = self.examples_to_dict(examples_list)
        self.assertIn('name', examples)
        self.assertIn('name.firstName', examples)
        self.assertIn('age', examples)

        input_json = '''
        {
            "name": {
                "firstName": "Ann",
                "lastName": "King"
            },
            "age": 20,
            "location":"us",
            "state": "ABC",
            "major": "CS"
        }
        '''
        json_obj = json.loads(input_json)
        max_examples = 3
        mock_config.set('max_examples', max_examples)
        builder = QueryTreeBuilder(mock_config)
        builder.build(json_obj)
        examples_list = builder.generate_examples(keyword_list, output_format)
        self.assertEqual(len(examples_list), max_examples)
        mock_config.set('max_examples', -1)

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
        builder = QueryTreeBuilder(mock_config)
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

    def test_dict_recommend_with_keywords(self):
        mock_config = MockConfig()
        keyword_list = ['name']
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
        builder = QueryTreeBuilder(mock_config)
        builder.build(json_obj)
        examples_list = builder.generate_examples(keyword_list, output_format)
        examples = self.examples_to_dict(examples_list)
        self.assertIn('name', examples)
        self.assertIn('name.firstName', examples)
        self.assertNotIn('age', examples)
        keyword_list = ['age']
        examples_list = builder.generate_examples(keyword_list, output_format)
        examples = self.examples_to_dict(examples_list)
        self.assertNotIn('name', examples)
        self.assertNotIn('name.firstName', examples)
        self.assertIn('age', examples)

    def test_query_examples(self):
        query_str = "[?contains(name,'Ann')==`true`]"
        help_str = 'This is the help message.'
        example = QueryExample(query_str, help_str)
        result_query_str = example._asdict().get("query string")
        self.assertEqual(result_query_str, "[?contains(name,'Ann')==\\`true\\`]")

        query_str = "This.is.a.very.very.very.long.query.string"
        help_str = "This is a very very very long help message."
        max_length = 10
        example = QueryExample(query_str, help_str)
        example.set_max_length(max_length, max_length)
        result_query_str = example._asdict().get("query string")
        result_help_str = example._asdict().get("help")
        self.assertLessEqual(len(result_query_str), max_length + 5)  # extra length for dots
        self.assertLessEqual(len(result_help_str), max_length + 5)  # extra length for dots


if __name__ == "__main__":
    unittest.main()
