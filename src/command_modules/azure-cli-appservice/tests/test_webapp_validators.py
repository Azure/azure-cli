# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock

from azure.cli.core._util import CLIError
from azure.cli.command_modules.appservice._validators import process_webapp_create_namespace

class TestValidators(unittest.TestCase):
    def test_create_web_with_plan_id(self):
        np = mock.MagicMock()
        np.location = 'antarctic'
        np.plan = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/g1/providers/Microsoft.Web/serverfarms/plan1'
        np.sku = None
        np.number_of_workers = None
        process_webapp_create_namespace(np)
        self.assertEqual(False, np.create_plan)

    def test_create_web_with_plan_error(self):
        np = mock.MagicMock()
        np.location = 'antarctic'
        np.plan = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/g1/providers/Microsoft.Web/serverfarms/plan1'
        np.sku = 'B1'
        np.number_of_workers = None
        with self.assertRaises(CLIError) as context:
            process_webapp_create_namespace(np)
        self.assertTrue('Usage error:' in str(context.exception))

