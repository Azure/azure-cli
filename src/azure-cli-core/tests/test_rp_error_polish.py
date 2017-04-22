# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import unittest
import mock

from azure.cli.core.commands import  _polish_rp_not_registerd_error


class TestRPErrorPolish(unittest.TestCase):

    def test_rp_error_polish(self):
        ex = mock.MagicMock()

        # bad error
        ex.response.content = b'bad error'
        result = _polish_rp_not_registerd_error(ex)
        self.assertTrue(ex == result)

        # good error (but not we are interested)
        ex.response.content = b'{"error":{"code":"c1","message":"m1"}}'
        result = _polish_rp_not_registerd_error(ex)
        self.assertTrue(ex == result)

        # the error we want to polish
        ex.response.content = (b'{"error":{"code":"MissingSubscriptionRegistration","message":'
                               b'"The subscription is not registered to use namespace '
                               b'\'Microsoft.Sql\'. See https://aka.ms/rps-not-found for how '
                               b'to register subscriptions."}}')
        result = _polish_rp_not_registerd_error(ex)
        self.assertEqual(
            str(result),
            "Run 'az provider register -n Microsoft.Sql' to register the namespace first")


if __name__ == '__main__':
    unittest.main()
