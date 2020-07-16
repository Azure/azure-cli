# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from . import http_bearer_challenge_cache as HttpBearerChallengeCache
from .http_challenge import HttpChallenge
from .http_bearer_challenge import HttpBearerChallenge
from .key_vault_authentication import KeyVaultAuthentication, KeyVaultAuthBase, AccessToken
from .http_message_security import generate_pop_key
from .key_vault_client import KeyVaultClient
from .version import VERSION

__all__ = ['KeyVaultClient',
           'KeyVaultId',
           'KeyId',
           'SecretId',
           'CertificateId',
           'CertificateIssuerId',
           'CertificateOperationId',
           'StorageAccountId',
           'StorageSasDefinitionId',
           'HttpBearerChallengeCache',
           'HttpBearerChallenge',
           'HttpChallenge',
           'KeyVaultAuthentication',
           'KeyVaultAuthBase',
           'generate_pop_key',
           'AccessToken']

__version__ = VERSION

