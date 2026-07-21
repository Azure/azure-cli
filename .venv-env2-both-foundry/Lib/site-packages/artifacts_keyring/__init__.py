# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import absolute_import

__author__ = "Microsoft Corporation <python@microsoft.com>"
__version__ = "1.0.0"

import warnings
from .support import urlsplit
from .plugin import CredentialProvider

import keyring.backend
import keyring.credentials


class ArtifactsKeyringBackend(keyring.backend.KeyringBackend):
    SUPPORTED_NETLOC = (
        "pkgs.dev.azure.com",
        "pkgs.visualstudio.com",
        "pkgs.codedev.ms",
        "pkgs.vsts.me"
    )
    _PROVIDER = CredentialProvider

    priority = 9.9


    def __init__(self):
        # In-memory cache of user-pass combination, to allow
        # fast handling of applications that insist on querying
        # username and password separately. get_password will
        # pop from this cache to avoid keeping the value
        # around for longer than necessary.
        self._cache = {}


    def get_credential(self, service, username):
        try:
            parsed = urlsplit(service)
        except Exception as exc:
            warnings.warn(str(exc))
            return None

        netloc = parsed.netloc.rpartition("@")[-1]

        if netloc is None or not netloc.endswith(self.SUPPORTED_NETLOC):
            return None

        provider = self._PROVIDER()

        username, password = provider.get_credentials(service)

        if username and password:
            self._cache[service, username] = password
            return keyring.credentials.SimpleCredential(username, password)


    def get_password(self, service, username):
        password = self._cache.get((service, username), None)
        if password is not None:
            return password

        creds = self.get_credential(service, None)
        if creds and username == creds.username:
            return creds.password

        return None


    def set_password(self, service, username, password):
        # Defer setting a password to the next backend
        raise NotImplementedError()


    def delete_password(self, service, username):
        # Defer deleting a password to the next backend
        raise NotImplementedError()
