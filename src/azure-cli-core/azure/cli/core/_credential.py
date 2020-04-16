# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.util import CLIError


def _create_identity_credential(**kwargs):
    from azure.identity import (
        AuthProfile,
        InteractiveBrowserCredential,
        ClientSecretCredential,
        ManagedIdentityCredential
    )
    authority = kwargs.pop("authority", None)
    tenant_id = kwargs.pop("tenant_id", None)
    home_account_id = kwargs.pop("home_account_id", None)
    if home_account_id:
        username = kwargs.pop("username", None)
        if not username or not authority or not tenant_id:
            raise CLIError("Missing username for user {}".format(home_account_id))
        auth_profile = AuthProfile(authority, home_account_id, tenant_id, username)
        return InteractiveBrowserCredential(profile=auth_profile, silent_auth_only=True,
                                            tenant_id=tenant_id, authority=authority)
    sp_id = kwargs.pop("sp_id", None)
    if sp_id:
        sp_key = kwargs.pop("sp_key", None)
        # todo: support use_cert_sn_issuer
        # use_cert_sn_issuer = kwargs.pop("use_cert_sn_issuer", None)
        if not sp_key or not tenant_id or not authority:
            raise CLIError("Missing service principle key for service principle {}".format(sp_id))
        return ClientSecretCredential(tenant_id, sp_id, sp_key, authority=authority)
    return ManagedIdentityCredential()


class IdentityCredential(object):    # pylint: disable=too-few-public-methods
    ''' abstract factory for Azure.Identity.Credential

    :keyword str authority
    '''

    def __init__(self, **kwargs):
        self._identityCredential = _create_identity_credential(**kwargs)

    def get_token(self, scope):
        return self._identityCredential.get_token(scope)
