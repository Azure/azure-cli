# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.util import CLIError
from msal import ClientApplication


class AdalRefreshTokenBasedClientApplication(ClientApplication):
    """
    This is added only for vmssh feature.
    It is a temporary solution and will deprecate after MSAL adopted completely.
    """
    def _acquire_token_silent_by_finding_rt_belongs_to_me_or_my_family(
            self, authority, scopes, account, **kwargs):
        # pylint: disable=line-too-long
        return self._acquire_token_silent_by_finding_specific_refresh_token(
            authority, scopes, None, **kwargs)

    def _acquire_token_silent_by_finding_specific_refresh_token(
            self, authority, scopes, query,
            rt_remover=None, break_condition=lambda response: False, **kwargs):
        refresh_token = kwargs.get('refresh_token', None)
        client = self._build_client(self.client_credential, authority)
        if 'refresh_token' in kwargs:
            kwargs.pop('refresh_token')
        if 'force_refresh' in kwargs:
            kwargs.pop('force_refresh')
        if 'correlation_id' in kwargs:
            kwargs.pop('correlation_id')
        response = client.obtain_token_by_refresh_token(refresh_token, scope=scopes, **kwargs)
        if "error" in response:
            raise CLIError(response["error"])
        return response
