import unittest
import unittest.util
import re

import unittest.test

from azure.cli.testsdk.checkers import JMESPathCheck, JMESPathCheckGreaterThan
from azure.cli.testsdk.exceptions import JMESPathCheckAssertionError

class TestCheckersWithNoneLikeValues(unittest.TestCase):
    def _format_exception_message_regex(self, key: str, expected_value: str, actual_value: any) -> str:
        return f"^Query '{re.escape(key)}' doesn't yield expected value '{re.escape(expected_value)}', instead the actual value is '{re.escape(str(actual_value))}'"

    def test_jmes_path_check_none_like_values(self):
        test_value_cases = [None, False, 0, "", [], {}]
        with unittest.mock.patch('azure.cli.testsdk.base.ExecutionResult') as mock_execution_result:
            for test_value in test_value_cases:
                mock_execution_result.get_output_in_json.return_value = { "key": test_value }
                check = JMESPathCheck("key", "value")

                with self.assertRaisesRegex(JMESPathCheckAssertionError, self._format_exception_message_regex("key", "value", test_value), msg=f"Testing value '{test_value}'"):
                    check(mock_execution_result)

    def test_jmes_path_check_not_there(self):
        with unittest.mock.patch('azure.cli.testsdk.base.ExecutionResult') as mock_execution_result:
            mock_execution_result.get_output_in_json.return_value = { }
            check = JMESPathCheck("key", "value")

            with self.assertRaisesRegex(JMESPathCheckAssertionError, self._format_exception_message_regex("key", "value", "None")):
                check(mock_execution_result)

    def test_jmes_path_check_normal_value(self):
        with unittest.mock.patch('azure.cli.testsdk.base.ExecutionResult') as mock_execution_result:
            mock_execution_result.get_output_in_json.return_value = { "key": "value" }
            check = JMESPathCheck("key", "not-value")
            with self.assertRaisesRegex(JMESPathCheckAssertionError, self._format_exception_message_regex("key", "not-value", "value")):
                check(mock_execution_result)

    def test_jmes_path_check_none_like_values(self):
        test_value_cases = [(False, True), (0, 1), ("", "value"), ([], [1])]
        with unittest.mock.patch('azure.cli.testsdk.base.ExecutionResult') as mock_execution_result:
            for test_value, check_value in test_value_cases:
                mock_execution_result.get_output_in_json.return_value = { "key": test_value }
                check = JMESPathCheckGreaterThan("key", check_value)

                with self.assertRaisesRegex(JMESPathCheckAssertionError, self._format_exception_message_regex("key", f"> {check_value}", test_value), msg=f"Testing value '{test_value}'"):
                    check(mock_execution_result)

    def test_jmes_path_check_greater_than_normal_value(self):
        with unittest.mock.patch('azure.cli.testsdk.base.ExecutionResult') as mock_execution_result:
            mock_execution_result.get_output_in_json.return_value = { "key": 5 }
            check = JMESPathCheckGreaterThan("key", 10)
            with self.assertRaisesRegex(JMESPathCheckAssertionError, self._format_exception_message_regex("key", "> 10", 5)):
                check(mock_execution_result)
