# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.aaz import AAZArgumentsSchema
from azure.cli.core.mock import DummyCli


class TestAAZCommandCtx(unittest.TestCase):

    def test_ctx_subscription(self):
        from azure.cli.core.aaz import AAZStrArg
        schema = AAZArgumentsSchema()
        schema.str1 = AAZStrArg()
        sub_id = "10101111-0000-0000-0000-000000000000"
        ctx = AAZCommandCtx(
            cli_ctx=DummyCli(),
            schema=schema,
            command_args={
                "subscription": sub_id,
            }
        )
        self.assertEqual(ctx._subscription_id, sub_id)
        self.assertEqual(ctx.subscription_id, sub_id)

        schema = AAZArgumentsSchema()
        schema.subscription = AAZStrArg()
        sub_id = "10101111-0000-0000-0000-000000000000"
        ctx = AAZCommandCtx(
            cli_ctx=DummyCli(),
            schema=schema,
            command_args={
                "subscription": sub_id,
            }
        )
        self.assertEqual(ctx.args.subscription, sub_id)
        self.assertEqual(ctx._subscription_id, None)
