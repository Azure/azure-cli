# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.credential import _generate_login_command


class TestUtils(unittest.TestCase):
    def test_generate_login_command(self):
        # No parameter is given
        assert _generate_login_command() == 'az login'

        base64_claims = "eyJhY2Nlc3NfdG9rZW4iOnsibmJmIjp7ImVzc2VudGlhbCI6dHJ1ZSwgInZhbHVlIjoiMTYxNzE3MjE1NiJ9fX0="
        json_claims = '{"access_token":{"nbf":{"essential":true, "value":"1617172156"}}}'
        expect = 'az login --claims eyJhY2Nlc3NfdG9rZW4iOnsibmJmIjp7ImVzc2VudGlhbCI6dHJ1ZSwgInZhbHVlIjoiMTYxNzE3MjE1NiJ9fX0='

        # Base64 string is preserved
        actual = _generate_login_command(claims=base64_claims)
        assert actual == expect

        # JSON string is converted to base64
        actual = _generate_login_command(claims=json_claims)
        assert actual == expect

        # scopes
        actual = _generate_login_command(scopes=["https://management.core.windows.net//.default"])
        assert actual == 'az login --scope https://management.core.windows.net//.default'
