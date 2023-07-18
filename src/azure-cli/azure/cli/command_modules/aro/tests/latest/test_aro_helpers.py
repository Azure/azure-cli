# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.command_modules.aro.custom import generate_random_id


class TestGenerateRandomIdHelper(unittest.TestCase):
    def test_random_id_length(self):
        random_id = generate_random_id()
        self.assertEqual(len(random_id), 8)

    def test_random_id_starts_with_letter(self):
        random_id = generate_random_id()
        self.assertTrue(random_id[0].isalpha())

    def test_random_id_is_alpha_num(self):
        random_id = generate_random_id()
        self.assertTrue(random_id.isalnum())
