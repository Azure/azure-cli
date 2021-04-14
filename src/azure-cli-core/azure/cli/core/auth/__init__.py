# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .credential import CredentialAdaptor
from .identity import Identity, AdalCredentialCache, MsalSecretStore, AZURE_CLI_CLIENT_ID
from .util import resource_to_scopes, aad_error_handler
