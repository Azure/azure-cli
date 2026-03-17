# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.core.aaz._error_format import AAZMgmtErrorFormat


class TestMgmtErrorFormat(unittest.TestCase):
    def test_additional_info_is_null(self):
        response = {
            "code": "BadRequest",
            "message": "Test.",
            "target": None,
            "details": None,
            "additionalInfo": None
        }

        error = AAZMgmtErrorFormat(response)
        self.assertTrue(str(error) == '(BadRequest) Test.\nCode: BadRequest\nMessage: Test.')
