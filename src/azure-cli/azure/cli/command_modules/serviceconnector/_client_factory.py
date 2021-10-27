# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core._profile import Profile


def cf_connection_cl(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.servicelinker import MicrosoftServiceLinker

    return get_mgmt_service_client(cli_ctx, MicrosoftServiceLinker, subscription_bound=False)


def cf_linker(cli_ctx, *_):
    return cf_connection_cl(cli_ctx).linker


def cf_linker_test_token(cli_ctx, *_):
    client = cf_connection_cl(cli_ctx).linker

    # pylint: disable=protected-access
    # HACK: set custom header to work around OBO
    profile = Profile(cli_ctx=cli_ctx)
    creds, _, _ = profile.get_raw_token()
    client._client._config.headers_policy._headers['x-ms-cupertino-test-token'] = creds[1]

    return client


def cf_linker_user_token(cli_ctx, *_):
    client = cf_connection_cl(cli_ctx).linker

    # pylint: disable=protected-access
    # set user token header
    profile = Profile(cli_ctx=cli_ctx)
    creds, _, _ = profile.get_raw_token()
    client._client._config.headers_policy._headers['x-ms-serviceconnector-user-token'] = creds[1]

    return client
