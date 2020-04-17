# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.util import CLIError
from knack.log import get_logger

from azure.identity import (
    AuthProfile,
    InteractiveBrowserCredential,
    DeviceCodeCredential,
    UsernamePasswordCredential,
    ClientSecretCredential,
    CertificateCredential,
    ManagedIdentityCredential
)

_CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'
logger = get_logger(__name__)


def login_with_interactive_browser(tenant_id):
    # Use InteractiveBrowserCredential
    if tenant_id:
        credential, auth_profile = InteractiveBrowserCredential.authenticate(
            client_id=_CLIENT_ID,
            tenant_id=tenant_id
        )
    else:
        credential, auth_profile = InteractiveBrowserCredential.authenticate(
            client_id=_CLIENT_ID,
            silent_auth_only=True
        )
    return credential, auth_profile


def login_with_device_code(tenant_id):
    # Use DeviceCodeCredential
    message = 'To sign in, use a web browser to open the page {} and enter the code {} to authenticate.'
    prompt_callback=lambda verification_uri, user_code, expires_on: \
        logger.warning(message.format(verification_uri, user_code))
    if tenant_id:
        cred, auth_profile = DeviceCodeCredential.authenticate(client_id=_CLIENT_ID,
                                                               tenant_id=tenant_id,
                                                               prompt_callback=prompt_callback)
    else:
        cred, auth_profile = DeviceCodeCredential.authenticate(client_id=_CLIENT_ID,
                                                               prompt_callback=prompt_callback)
    return cred, auth_profile


def login_with_username_password(username, password, tenant_id):
    # Use UsernamePasswordCredential
    if tenant_id:
        credential, auth_profile = UsernamePasswordCredential.authenticate(_CLIENT_ID, username, password,
                                                                           tenant_id=tenant_id)
    else:
        credential, auth_profile = UsernamePasswordCredential.authenticate(_CLIENT_ID, username, password)
    return credential, auth_profile


def login_with_msi():
    # Use ManagedIdentityCredential
    pass


def get_user_credential(authority, home_account_id, tenant_id, username):
    auth_profile = AuthProfile(authority, home_account_id, tenant_id, username)
    return InteractiveBrowserCredential(profile=auth_profile, silent_auth_only=True)


def get_service_principal_credential(tenant_id, client_id, client_secret, certificate_path, use_cert_sn_issuer):
    if client_secret:
        return ClientSecretCredential(tenant_id, client_id, client_secret, use_cert_sn_issuer=use_cert_sn_issuer)
    if certificate_path:
        return CertificateCredential(tenant_id, client_id, certificate_path)


def get_msi_credential():
    pass
