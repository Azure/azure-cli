# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from unittest.mock import patch

from azure.cli.command_modules.acs.tests.latest.custom_preparers import (
    AKSCustomResourceGroupPreparer,
    AKSCustomRoleBasedServicePrincipalPreparer,
    ENV_VAR_FORCE_RESOURCE_GROUP_LOCATION,
    _normalize_optional_live_test_setting,
)


class TestNormalizeOptionalLiveTestSetting(unittest.TestCase):

    def test_empty_placeholders_are_normalized(self):
        for value in (None, "", "  ", "''", '""', "\\'\\'", '\\"\\"'):
            with self.subTest(value=value):
                self.assertIsNone(_normalize_optional_live_test_setting(value))

    def test_valid_value_is_preserved(self):
        self.assertEqual(_normalize_optional_live_test_setting(" value "), "value")

    @patch.dict(os.environ, {
        "AZURE_CLI_TEST_DEV_SP_NAME": '\\"\\"',
        "AZURE_CLI_TEST_DEV_SP_PASSWORD": '\\"\\"',
    })
    def test_service_principal_preparer_rejects_quoted_empty_credentials(self):
        preparer = AKSCustomRoleBasedServicePrincipalPreparer()

        self.assertIsNone(preparer.dev_setting_sp_name)
        self.assertIsNone(preparer.dev_setting_sp_password)

        def test_case():
            pass

        skipped_test_case = preparer(test_case)
        self.assertTrue(skipped_test_case.__unittest_skip__)


class TestAKSCustomResourceGroupPreparer(unittest.TestCase):

    def _create_preparer(self, preserve_default_location):
        return AKSCustomResourceGroupPreparer(
            location="westus2",
            preserve_default_location=preserve_default_location,
        )

    @patch.dict(os.environ, {
        "AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION": "eastus",
    }, clear=True)
    def test_default_location_override_is_used(self):
        preparer = self._create_preparer(preserve_default_location=False)

        self.assertEqual(preparer.location, "eastus")
        self.assertEqual(preparer.dev_setting_location, "eastus")

    @patch.dict(os.environ, {
        "AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION": "eastus",
    }, clear=True)
    def test_preserved_location_wins_over_default_override(self):
        preparer = self._create_preparer(preserve_default_location=True)

        self.assertEqual(preparer.location, "westus2")
        self.assertEqual(preparer.dev_setting_location, "westus2")

    @patch.dict(os.environ, {
        ENV_VAR_FORCE_RESOURCE_GROUP_LOCATION: "westcentralus",
        "AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION": "eastus",
    }, clear=True)
    def test_force_location_wins_over_default_override(self):
        preparer = self._create_preparer(preserve_default_location=False)

        self.assertEqual(preparer.location, "westcentralus")
        self.assertEqual(preparer.dev_setting_location, "westcentralus")

    @patch.dict(os.environ, {
        ENV_VAR_FORCE_RESOURCE_GROUP_LOCATION: "westcentralus",
        "AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION": "eastus",
    }, clear=True)
    def test_force_location_wins_over_preserved_location(self):
        preparer = self._create_preparer(preserve_default_location=True)

        self.assertEqual(preparer.location, "westcentralus")
        self.assertEqual(preparer.dev_setting_location, "westcentralus")


if __name__ == "__main__":
    unittest.main()
