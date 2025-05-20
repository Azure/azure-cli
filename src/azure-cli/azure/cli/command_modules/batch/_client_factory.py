# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def mgmt_batch_account_client_factory(cli_ctx, _):
    return batch_mgmt_client_factory(cli_ctx).batch_account


def mgmt_pool_client_factory(cli_ctx, _):
    return batch_mgmt_client_factory(cli_ctx).pool


def mgmt_private_link_resource_client_factory(cli_ctx, _):
    return batch_mgmt_client_factory(cli_ctx).private_link_resource


def mgmt_private_endpoint_connection_client_factory(cli_ctx, _):
    return batch_mgmt_client_factory(cli_ctx).private_endpoint_connection


def mgmt_application_client_factory(cli_ctx, _):
    return batch_mgmt_client_factory(cli_ctx).application


def mgmt_application_package_client_factory(cli_ctx, _):
    return batch_mgmt_client_factory(cli_ctx).application_package


def mgmt_location_client_factory(cli_ctx, _):
    return batch_mgmt_client_factory(cli_ctx).location


def batch_mgmt_client_factory(cli_ctx, **_):
    from azure.mgmt.batch import BatchManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, BatchManagementClient)


def batch_data_client_factory(cli_ctx, kwargs):
    from azure.batch import BatchClient

    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    account_endpoint = kwargs.pop('account_endpoint', None)
    token_credential = kwargs.pop('token_credential', None)

    credential = None

    if not token_credential and not account_key:
        from azure.cli.core._profile import Profile
        profile = Profile(cli_ctx=cli_ctx)
        token_credential, _, _ = profile.get_login_credentials()

    if account_key:
        from azure.core.credentials import AzureNamedKeyCredential
        credential = AzureNamedKeyCredential(name=account_name, key=account_key)
    else:
        credential = token_credential

    if not (account_endpoint.startswith('https://') or
            account_endpoint.startswith('http://')):
        account_endpoint = 'https://' + account_endpoint

    from azure.cli.core.auth.util import resource_to_scopes
    return BatchClient(credential=credential, endpoint=account_endpoint.rstrip('/'),
                       credential_scopes=resource_to_scopes(cli_ctx.cloud.endpoints.batch_resource_id))
