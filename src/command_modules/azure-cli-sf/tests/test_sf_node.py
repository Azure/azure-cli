# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import azure.cli.command_modules.sf.custom as sf_c


class SfNodeTests(unittest.TestCase):
    def none_package_sharing_policies_returns_none_test(self):
        self.assertIs(sf_c.parse_package_sharing_policies(None), None)

    def empty_package_sharing_policies_returns_none_test(self):
        self.assertIs(sf_c.parse_package_sharing_policies([]), None)

    def single_package_sharing_policy_returns_single_test(self):
        from azure.servicefabric.models.package_sharing_policy_info import PackageSharingPolicyInfo

        res = sf_c.parse_package_sharing_policies([{"name": "derp_a", "scope": "None"}])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].shared_package_name, "derp_a")
        self.assertEqual(res[0].package_sharing_scope, "None")
