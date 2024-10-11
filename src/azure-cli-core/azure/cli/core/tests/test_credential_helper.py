# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from azure.cli.core.credential_helper import distinguish_credential, redact_credential_for_string, redact_credential


class TestCredentialHelper(unittest.TestCase):
    def _get_test_secret_masker(self):
        from microsoft_security_utilities_secret_masker import SecretMasker, load_regex_pattern_from_json
        email_address_json = {
            "Pattern": r"(?<refine>[\w.%#+-]+)(%40|@)([a-z0-9.-]*.[a-z]{2,})",
            "Id": "001",
            "Name": "EmailAddress",
            "Signatures": [
                "@",
                "%40"
            ],
            "DetectionMetadata": "HighConfidence"
        }
        guid_json = {
            "Pattern": r"(?<refine>[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})",
            "Id": "002",
            "Name": "GUID",
            "DetectionMetadata": "LowConfidence"
        }
        email_address_pattern = load_regex_pattern_from_json(email_address_json)
        guid_pattern = load_regex_pattern_from_json(guid_json)
        return SecretMasker(regex_secrets=(email_address_pattern, guid_pattern))

    def test_detect_credential_for_string(self):
        with mock.patch('azure.cli.core.credential_helper.get_secret_masker', side_effect=self._get_test_secret_masker):
            creation_time = '2024-03-07T02:50:56.464790+00:00'
            containing_credential, _, _ = distinguish_credential(creation_time)
            self.assertEqual(containing_credential, False)

            email = 'test@AzureSDKTest.com'
            containing_credential, _, _ = distinguish_credential(email)
            self.assertEqual(containing_credential, True)

    def test_redact_credential_for_string(self):
        with mock.patch('azure.cli.core.credential_helper.get_secret_masker', side_effect=self._get_test_secret_masker):
            creation_time = '2024-03-07T02:50:56.464790+00:00'
            result = redact_credential_for_string(creation_time)
            self.assertEqual(result, creation_time)

            email = 'test@AzureSDKTest.com'
            result = redact_credential_for_string(email)
            self.assertEqual(result,'+++@AzureSDKTest.com')

            object_id = '3707fb2f-ac10-4591-a04f-8b0d786ea37d'
            result = redact_credential_for_string(object_id)
            self.assertEqual(result, '+++')

    def test_redact_credential_for_json(self):
        content = {
            'tenant': '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a',
            'account_name': 'testaccount',
            'email_address': 'testaccount@AzureSDKTest.com'
        }
        expected_content = {
            'tenant': '+++',
            'account_name': 'testaccount',
            'email_address': '+++@AzureSDKTest.com'
        }
        with mock.patch('azure.cli.core.credential_helper.get_secret_masker', side_effect=self._get_test_secret_masker):
            self.assertEqual(redact_credential(content), expected_content)
