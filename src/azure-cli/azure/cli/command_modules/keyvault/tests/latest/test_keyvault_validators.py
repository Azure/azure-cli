# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
from unittest import TestCase, mock

from knack.util import CLIError


class DeletedVaultOrHsmValidatorTest(TestCase):
    def test_validate_deleted_vault_or_hsm_name_without_name(self):
        from azure.cli.command_modules.keyvault._validators import validate_deleted_vault_or_hsm_name

        ns = argparse.Namespace(vault_name=None, hsm_name=None)
        with self.assertRaisesRegex(CLIError, 'Please specify --name or --hsm-name.'):
            validate_deleted_vault_or_hsm_name(mock.Mock(), ns)
