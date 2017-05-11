# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import azure.cli.command_modules.sf.custom as sf_c
from azure.cli.core.util import CLIError


class SfAppTests(unittest.TestCase):

    def empty_parse_params_returns_empty_test(self):
        self.assertEqual(sf_c.parse_app_params({}), [])

    def none_parse_params_returns_none_test(self):
        self.assertIsNone(sf_c.parse_app_params(None))

    def parse_params_returns_app_param_test(self):
        res = sf_c.parse_app_params({"tree": "green"})
        self.assertEqual(len(res), 1)
