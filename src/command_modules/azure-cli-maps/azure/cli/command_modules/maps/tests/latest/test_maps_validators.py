# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from argparse import Namespace
from knack.util import CLIError
from azure.cli.command_modules.maps.validators import validate_account_name, ACCOUNT_NAME_MAX_LENGTH


class TestValidators(unittest.TestCase):
    def setUp(self):
        self.namespace = Namespace()

    def _assert_invalid_account_names(self, invalid_names):
        for invalid_name in invalid_names:
            self.namespace.account_name = invalid_name
            self.assertRaises(CLIError, lambda: validate_account_name(self.namespace))

    def _assert_valid_account_names(self, valid_names):
        for valid_name in valid_names:
            self.namespace.account_name = valid_name
            try:
                validate_account_name(self.namespace)
            except CLIError:
                self.fail("validate_account_name() raised CLIError unexpectedly!")

    def test_validate_account_name_length(self):
        invalid_names = ["", "a", "a" * (ACCOUNT_NAME_MAX_LENGTH + 1)]
        valid_names = ["Valid-Account-Name", "aa", "a" * ACCOUNT_NAME_MAX_LENGTH]

        self._assert_invalid_account_names(invalid_names)
        self._assert_valid_account_names(valid_names)

    def test_validate_account_name_regex(self):
        invalid_names = ["_A", "úñícódé", "ΞΞ", "resumé", "American cheese"]
        valid_names = ["Bergenost", "Cheddar_cheese", "Colby-Jack", "Cottage.cheese", "Cr34MCh3353", "montereyjack"]

        self._assert_invalid_account_names(invalid_names)
        self._assert_valid_account_names(valid_names)


if __name__ == '__main__':
    unittest.main()
