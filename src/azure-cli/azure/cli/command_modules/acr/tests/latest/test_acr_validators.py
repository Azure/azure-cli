# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.cloud import HARD_CODED_CLOUD_LIST
from azure.cli.command_modules.acr._validators import validate_registry_name

class AcrValidatorsTests(unittest.TestCase):  
    def test_registry_name_with_dnl_suffix_loginserver(self):
        namespace = SimpleNamespace(
            **{
                "registry_name": "myacr-dnlhash123.azurecr.io",
            }
        )
        azure_public_cloud = HARD_CODED_CLOUD_LIST[0]
        cmd = Mock(cli_ctx=Mock(cloud=azure_public_cloud))
        validate_registry_name(cmd, namespace)
        self.assertEqual(namespace.registry_name, 'myacr')

    def test_registry_name_valid_inputs(self):
        """Test valid registry names that should pass validation."""
        test_cases = [
            # (input_registry_name, expected_output)
            ("validregistry.azurecr.io", "validregistry"),
            ("myregistry123-dnlhasd234.azurecr.io", "myregistry123"),
            ("test5chars", "test5chars"),
            ("a" * 50, "a" * 50),  # Maximum length
            ("registry2024", "registry2024"),
        ]
        
        azure_public_cloud = HARD_CODED_CLOUD_LIST[0]
        cmd = Mock(cli_ctx=Mock(cloud=azure_public_cloud))
        
        for input_name, expected_output in test_cases:
            with self.subTest(input_name=input_name):
                namespace = SimpleNamespace(registry_name=input_name)
                validate_registry_name(cmd, namespace)
                self.assertEqual(namespace.registry_name, expected_output)
    
    def test_registry_name_invalid_inputs_should_raise_error(self):
        """Test invalid registry names that should raise InvalidArgumentValueError."""
        invalid_inputs = [
            "myregistry-hash123",  # Has hyphen but no suffix
            "test.invalid.suffix",  # Invalid suffix
            "registry.azurecr.io124567",  # Wrong suffix
            "my-registry.wrongsuffix.io",  # Invalid suffix with hyphen
            "78787%^&*(()).azurecr.io" # invalid characters
        ]
        
        azure_public_cloud = HARD_CODED_CLOUD_LIST[0]
        cmd = Mock(cli_ctx=Mock(cloud=azure_public_cloud))
        
        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                namespace = SimpleNamespace(registry_name=invalid_input)
                with self.assertRaises(InvalidArgumentValueError):
                    validate_registry_name(cmd, namespace)
