# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock

from azure.cli.command_modules.hint.custom import _get_default_account_text


class HintTest(unittest.TestCase):

    def test_get_default_account_text(self):
        test_accounts = [
            # Subscription with unique name
            {
                "cloudName": "AzureCloud",
                "homeTenantId": "ca97aaa0-5a12-4ae3-8929-c8fb57dd93d6",
                "id": "2b8e6bbc-631a-4bf6-b0c6-d4947b3c79dd",
                "isDefault": False,
                "managedByTenants": [],
                "name": "Unique Name",
                "state": "Enabled",
                "tenantId": "ca97aaa0-5a12-4ae3-8929-c8fb57dd93d6",
                "user": {
                    "name": "test@microsoft.com",
                    "type": "user"
                }
            },
            # Subscription with duplicated name
            {
                "cloudName": "AzureCloud",
                "homeTenantId": "ca97aaa0-5a12-4ae3-8929-c8fb57dd93d6",
                "id": "414af076-009b-4282-9a0a-acf75bcb037e",
                "isDefault": False,
                "managedByTenants": [],
                "name": "Duplicated Name",
                "state": "Enabled",
                "tenantId": "ca97aaa0-5a12-4ae3-8929-c8fb57dd93d6",
                "user": {
                    "name": "test@microsoft.com",
                    "type": "user"
                }
            },
            # Subscription with duplicated name
            {
                "cloudName": "AzureCloud",
                "homeTenantId": "54826b22-38d6-4fb2-bad9-b7b93a3e9c5a",
                "id": "0b1f6471-1bf0-4dda-aec3-cb9272f09590",
                "isDefault": False,
                "managedByTenants": [],
                "name": "Duplicated Name",
                "state": "Enabled",
                "tenantId": "54826b22-38d6-4fb2-bad9-b7b93a3e9c5a",
                "user": {
                    "name": "test@microsoft.com",
                    "type": "user"
                }
            },
            # Tenant
            {
                "cloudName": "AzureCloud",
                "id": "246b1785-9030-40d8-a0f0-d94b15dc002c",
                "isDefault": False,
                "name": "N/A(tenant level account)",
                "state": "Enabled",
                "tenantId": "246b1785-9030-40d8-a0f0-d94b15dc002c",
                "user": {
                    "name": "test@microsoft.com",
                    "type": "user"
                }
            }
        ]
        expected_result = [
            ("subscription", "Unique Name"),
            ("subscription", "Duplicated Name (414af076-009b-4282-9a0a-acf75bcb037e)"),
            ("subscription", "Duplicated Name (0b1f6471-1bf0-4dda-aec3-cb9272f09590)"),
            ("tenant", "246b1785-9030-40d8-a0f0-d94b15dc002c")
        ]

        for i in range(len(test_accounts)):
            # Mark each account as default and check the result
            with mock.patch.dict(test_accounts[i], {'isDefault': True}):
                self.assertEqual(_get_default_account_text(test_accounts), expected_result[i])
