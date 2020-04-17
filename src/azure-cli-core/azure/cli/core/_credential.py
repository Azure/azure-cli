# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.util import CLIError


class IdentityCredential(object):    # pylint: disable=too-few-public-methods
    ''' abstract factory for Azure.Identity.Credential

    :keyword str authority
    '''

    def __init__(self, **kwargs):
        from azure.identity import (
            AuthProfile,
            InteractiveBrowserCredential,
            ClientSecretCredential,
            CertificateCredential,
            ManagedIdentityCredential
        )
        authority = kwargs.pop("authority", None)
        tenant_id = kwargs.pop("tenant_id", None)
        home_account_id = kwargs.pop("home_account_id", None)
        client_id = kwargs.pop("client_id", None)
        if home_account_id:
            # User
            username = kwargs.pop("username", None)
            if not username or not authority or not tenant_id:
                raise CLIError("Missing username for user {}".format(home_account_id))
            auth_profile = AuthProfile(authority, home_account_id, tenant_id, username)
            self._identityCredential = InteractiveBrowserCredential(profile=auth_profile, silent_auth_only=True,
                                                                    tenant_id=tenant_id, authority=authority)
        elif client_id:
            # Service Principal
            client_secret = kwargs.pop("client_secret", None)
            certificate_path = kwargs.pop("certificate_path", None)
            # todo: support use_cert_sn_issuer
            # use_cert_sn_issuer = kwargs.pop("use_cert_sn_issuer", None)
            if client_secret:
                self._identityCredential = ClientSecretCredential(tenant_id, client_id, client_secret, authority=authority)
            if certificate_path:
                self._identityCredential = CertificateCredential(tenant_id, client_id, certificate_path, authority=authority)
        else:
            # MSI
            self._identityCredential = ManagedIdentityCredential()

    def get_token(self, scope):
        return self._identityCredential.get_token(scope)
