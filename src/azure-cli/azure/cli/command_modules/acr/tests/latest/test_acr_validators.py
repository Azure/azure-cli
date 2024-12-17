# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from azure.cli.core.cloud import HARD_CODED_CLOUD_LIST
from azure.cli.command_modules.acr._validators import validate_registry_name

class AcrValidatorsTests(unittest.TestCase):
    def test_registry_name_with_dnl_suffix(self):
        acr_supported_clouds = [cloud for cloud in HARD_CODED_CLOUD_LIST if cloud.name != 'AzureGermanCloud']
        for hard_coded_cloud in acr_supported_clouds:
            namespace = SimpleNamespace(
                    **{
                        "registry_name": "myacr-dnlhash123",
                    }
                )
            cmd = Mock(cli_ctx=Mock(cloud=hard_coded_cloud))
            validate_registry_name(cmd, namespace)
            self.assertEqual(namespace.registry_name, 'myacr')
    
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

