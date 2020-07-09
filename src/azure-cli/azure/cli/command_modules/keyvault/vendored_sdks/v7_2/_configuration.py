# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.core.configuration import Configuration
from azure.core.pipeline import policies

from ..challenge_auth_policy import ChallengeAuthPolicy

from .version import VERSION


class KeyVaultClientConfiguration(Configuration):
    """Configuration for KeyVaultClient
    Note that all parameters used to create this instance are saved as instance
    attributes.

    :param credentials: Credentials needed for the client to connect to Azure.
    :type credentials: :mod:`A msrestazure Credentials
     object<msrestazure.azure_active_directory>`
    """

    def __init__(self, credentials, **kwargs):

        if credentials is None:
            raise ValueError("Parameter 'credentials' must not be None.")

        super(KeyVaultClientConfiguration, self).__init__(**kwargs)

        self.credentials = credentials
        self._configure(**kwargs)

        self.user_agent_policy.add_user_agent('azsdk-python-azure-keyvault/{}'.format(VERSION))
        self.generate_client_request_id = True

    def _configure(self, **kwargs):
        self.user_agent_policy = kwargs.get('user_agent_policy') or policies.UserAgentPolicy(**kwargs)
        self.headers_policy = kwargs.get('headers_policy') or policies.HeadersPolicy(**kwargs)
        self.proxy_policy = kwargs.get('proxy_policy') or policies.ProxyPolicy(**kwargs)
        self.logging_policy = kwargs.get('logging_policy') or policies.NetworkTraceLoggingPolicy(**kwargs)
        self.retry_policy = kwargs.get('retry_policy') or policies.RetryPolicy(**kwargs)
        self.custom_hook_policy = kwargs.get('custom_hook_policy') or policies.CustomHookPolicy(**kwargs)
        self.redirect_policy = kwargs.get('redirect_policy') or policies.RedirectPolicy(**kwargs)
        self.authentication_policy = kwargs.get('authentication_policy') or ChallengeAuthPolicy(self.credentials)
