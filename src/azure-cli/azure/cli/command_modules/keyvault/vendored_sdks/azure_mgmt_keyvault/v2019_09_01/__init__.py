# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._configuration import KeyVaultManagementClientConfiguration
from ._key_vault_management_client import KeyVaultManagementClient
__all__ = ['KeyVaultManagementClient', 'KeyVaultManagementClientConfiguration']

from .version import VERSION

__version__ = VERSION

