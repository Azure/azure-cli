# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest

from azure.cli.core import azclierror
from azure.cli.core.aaz import exceptions as aazerror
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.aaz import AAZArgumentsSchema
from azure.cli.core.mock import DummyCli


class TestAAZArgFmt(unittest.TestCase):

    @staticmethod
    def format_arg(schema, data):
        ctx = AAZCommandCtx(
            cli_ctx=DummyCli(), schema=schema,
            command_args=data
        )
        ctx.format_args()
        return ctx.args

    def test_str_fmt(self):
        from azure.cli.core.aaz import AAZStrArg, AAZStrArgFormat
        schema = AAZArgumentsSchema()
        schema.str1 = AAZStrArg(
            fmt=AAZStrArgFormat(
                pattern="[a-z]+",
                max_length=8,
                min_length=2,
            )
        )

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"str1": ""})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"str1": "1234"})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"str1": "abcdefghi"})

        with self.assertRaises(aazerror.AAZInvalidArgValueError):
            self.format_arg(schema, {"str1": "aBCD"})

        args = self.format_arg(schema, {"str1": "abcdefgh"})
        self.assertEqual(args.str1, "abcdefgh")

        args = self.format_arg(schema, {"str1": "abcd"})
        self.assertEqual(args.str1, "abcd")
