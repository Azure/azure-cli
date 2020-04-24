# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""
This is added only for vmssh feature.
This is a temporary solution and will deprecate after adoption to MSAL completely.
The function is try to retrieve MSAL access token with ADAL refresh token.
"""
from knack import log


logger = log.get_logger(__name__)


def get_ssh_credentials(cli_ctx, scopes, data):
    from azure.cli.core._profile import Profile
    logger.debug("Getting SSH credentials")
    profile = Profile(cli_ctx=cli_ctx)

    user, cert = profile.get_ssh_credentials(scopes, data)
    return SSHCredentials(user, cert)


class SSHCredentials(object):
    # pylint: disable=too-few-public-methods

    def __init__(self, username, cert):
        self.username = username
        self.certificate = "ssh-rsa-cert-v01@openssh.com " + cert
