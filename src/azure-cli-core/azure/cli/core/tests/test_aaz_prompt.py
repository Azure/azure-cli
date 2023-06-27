# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import base64
import json
import random

import unittest
try:
    import mock
except ImportError:
    from unittest import mock

from azure.cli.core import azclierror
from azure.cli.core.aaz import exceptions as aazerror
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.aaz import AAZArgumentsSchema
from azure.cli.core.mock import DummyCli
from azure.cli.core.aaz._prompt import AAZPromptInput, AAZPromptPasswordInput


class TestAAZPromptInput(unittest.TestCase):

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_prompt_input(self, _):
        from azure.cli.core.aaz._arg import AAZStrArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz import has_value
        schema = AAZArgumentsSchema()
        v = schema()

        schema.prompt_arg = AAZStrArg(
            options=["--prompt-arg"],
            enum={
                "1": "Monday",
                "2": "Tuesday",
                "3": "Wednesday",
                "4": "Thursday",
                "5": "Friday",
                "6": "Saturday",
                "7": "Sunday",
                "Mon": "Monday",
                "Tue": "Tuesday",
                "Wed": "Wednesday",
                "Thu": "Thursday",
                "Fri": "Friday",
                "Sat": "Saturday",
                "Sun": "Sunday",
            },
            required=True,
            blank=AAZPromptInput(msg="Your input value for --prompt-arg:")
        )

        self.assertFalse(has_value(v.prompt_arg))

        arg = schema.prompt_arg.to_cmd_arg("prompt_arg")
        self.assertEqual(len(arg.choices), 14)
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, None)

        expected_result = '1'
        with mock.patch('knack.prompting._input', return_value=expected_result):
            dest_ops.apply(v, "prompt_arg")
        self.assertEqual(v.prompt_arg, "Monday")

        expected_result = '100'
        with self.assertRaisesRegex(azclierror.InvalidArgumentValueError, f"unrecognized value '{expected_result}' from choices"):
            with mock.patch('knack.prompting._input', return_value=expected_result):
                dest_ops.apply(v, "prompt_arg")

    @mock.patch('sys.stdin.isatty', return_value=False)
    def test_no_tty_prompt_input(self, _):
        from azure.cli.core.aaz._arg import AAZStrArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz import has_value
        schema = AAZArgumentsSchema()
        v = schema()

        schema.prompt_arg = AAZStrArg(
            options=["--prompt-arg"],
            enum={
                "1": "Monday",
                "2": "Tuesday",
                "3": "Wednesday",
                "4": "Thursday",
                "5": "Friday",
                "6": "Saturday",
                "7": "Sunday",
                "Mon": "Monday",
                "Tue": "Tuesday",
                "Wed": "Wednesday",
                "Thu": "Thursday",
                "Fri": "Friday",
                "Sat": "Saturday",
                "Sun": "Sunday",
            },
            required=True,
            blank=AAZPromptInput(msg="Your input value for --prompt-arg:")
        )

        self.assertFalse(has_value(v.prompt_arg))

        arg = schema.prompt_arg.to_cmd_arg("prompt_arg")
        self.assertEqual(len(arg.choices), 14)
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, None)

        expected_result = '1'
        with self.assertRaisesRegex(aazerror.AAZInvalidValueError, f"argument value cannot be blank in non-interactive mode."):
            with mock.patch('knack.prompting._input', return_value=expected_result):
                dest_ops.apply(v, "prompt_arg")

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_pass_prompt_input(self, _):
        from azure.cli.core.aaz._arg import AAZPasswordArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz._arg_fmt import AAZStrArgFormat
        from azure.cli.core.aaz import has_value
        schema = AAZArgumentsSchema()
        v = schema()

        schema.password = AAZPasswordArg(
            options=["--password"],
            required=True,
            blank=AAZPromptPasswordInput(msg="Your input value for --password:")
        )

        self.assertFalse(has_value(v.password))

        arg = schema.password.to_cmd_arg("password")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, None)

        my_password = '123'
        with mock.patch('getpass.getpass', return_value=my_password):
            dest_ops.apply(v, "password")
        self.assertEqual(v.password, my_password)

    @mock.patch('sys.stdin.isatty', return_value=True)
    def test_pass_prompt_input_confirm(self, _):
        from azure.cli.core.aaz._arg import AAZPasswordArg, AAZArgumentsSchema
        from azure.cli.core.aaz._arg_action import AAZArgActionOperations
        from azure.cli.core.aaz._arg_fmt import AAZStrArgFormat
        from azure.cli.core.aaz import has_value
        schema = AAZArgumentsSchema()
        v = schema()

        schema.password = AAZPasswordArg(
            options=["--password"],
            required=True,
            blank=AAZPromptPasswordInput(msg="Your input value for --password:", confirm=True)
        )

        self.assertFalse(has_value(v.password))

        arg = schema.password.to_cmd_arg("password")
        action = arg.type.settings["action"]

        dest_ops = AAZArgActionOperations()
        self.assertEqual(len(dest_ops._ops), 0)

        action.setup_operations(dest_ops, None)

        my_password = '123'
        with mock.patch('getpass.getpass', side_effect=[my_password, my_password]):
            dest_ops.apply(v, "password")
        self.assertEqual(v.password, my_password)

        my_password1 = '111'
        my_password2 = '123'
        with self.assertRaises(StopIteration):
            with mock.patch('getpass.getpass', side_effect=[my_password1, my_password2]):
                dest_ops.apply(v, "password")
