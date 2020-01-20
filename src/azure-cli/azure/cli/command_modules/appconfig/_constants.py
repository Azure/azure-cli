# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods

"""Reserved keywords in the AppConfiguration service.
"""


class FeatureFlagConstants:
    FEATURE_FLAG_PREFIX = ".appconfig.featureflag/"
    FEATURE_FLAG_CONTENT_TYPE = "application/vnd.microsoft.appconfig.ff+json;charset=utf-8"


class KeyVaultConstants:
    KEYVAULT_CONTENT_TYPE = "application/vnd.microsoft.appconfig.keyvaultref+json;charset=utf-8"
    APPSVC_KEYVAULT_PREFIX = "@Microsoft.KeyVault"
