# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import in_cloud_console


def mgmt_batch_account_client_factory(cli_ctx, _):
    return batch_client_factory(cli_ctx).batch_account


def mgmt_application_client_factory(cli_ctx, _):
    return batch_client_factory(cli_ctx).application


def mgmt_application_package_client_factory(cli_ctx, _):
    return batch_client_factory(cli_ctx).application_package


def mgmt_location_client_factory(cli_ctx, _):
    return batch_client_factory(cli_ctx).location


def application_client_factory(cli_ctx, kwargs):
    return batch_data_service_factory(cli_ctx, kwargs).application


def account_client_factory(cli_ctx, kwargs):
    return batch_data_service_factory(cli_ctx, kwargs).account


def certificate_client_factory(cli_ctx, kwargs):
    return batch_data_service_factory(cli_ctx, kwargs).certificate


def pool_client_factory(cli_ctx, kwargs):
    return batch_data_service_factory(cli_ctx, kwargs).pool


def job_client_factory(cli_ctx, kwargs):
    return batch_data_service_factory(cli_ctx, kwargs).job


def job_schedule_client_factory(cli_ctx, kwargs):
    return batch_data_service_factory(cli_ctx, kwargs).job_schedule


def task_client_factory(cli_ctx, kwargs):
    return batch_data_service_factory(cli_ctx, kwargs).task


def file_client_factory(cli_ctx, kwargs):
    return batch_data_service_factory(cli_ctx, kwargs).file


def compute_node_client_factory(cli_ctx, kwargs):
    return batch_data_service_factory(cli_ctx, kwargs).compute_node


def batch_client_factory(cli_ctx, **_):
    from azure.mgmt.batch import BatchManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, BatchManagementClient)


def batch_data_service_factory(cli_ctx, kwargs):
    import azure.batch.batch_service_client as batch
    import azure.batch.batch_auth as batchauth

    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    account_endpoint = kwargs.pop('account_endpoint', None)
    kwargs.pop('yes', None)

    credentials = None
    if not account_key:
        from azure.cli.core._profile import Profile
        profile = Profile(cli_ctx=cli_ctx)
        # in order to use AAD auth in cloud shell mode, we will use mgmt AAD token
        # instead of Batch AAD token to auth
        if in_cloud_console():
            resource = cli_ctx.cloud.endpoints.active_directory_resource_id
        else:
            resource = cli_ctx.cloud.endpoints.batch_resource_id
        credentials, _, _ = profile.get_login_credentials(resource=resource)
    else:
        credentials = batchauth.SharedKeyCredentials(account_name, account_key)
    if not account_endpoint.startswith('https://'):
        account_endpoint = 'https://' + account_endpoint
    return batch.BatchServiceClient(credentials, base_url=account_endpoint)
