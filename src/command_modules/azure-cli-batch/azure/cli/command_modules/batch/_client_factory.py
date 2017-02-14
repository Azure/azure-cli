# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def account_mgmt_client_factory(kwargs):
    return batch_client_factory(**kwargs).batch_account


def application_mgmt_client_factory(kwargs):
    return batch_client_factory(**kwargs).application


def application_package_client_factory(kwargs):
    return batch_client_factory(**kwargs).application_package


def location_client_factory(kwargs):
    return batch_client_factory(**kwargs).location


def application_client_factory(kwargs):
    return batch_data_service_factory(kwargs).application


def account_client_factory(kwargs):
    return batch_data_service_factory(kwargs).account


def certificate_client_factory(kwargs):
    return batch_data_service_factory(kwargs).certificate


def pool_client_factory(kwargs):
    return batch_data_service_factory(kwargs).pool


def job_client_factory(kwargs):
    return batch_data_service_factory(kwargs).job


def job_schedule_client_factory(kwargs):
    return batch_data_service_factory(kwargs).job_schedule


def task_client_factory(kwargs):
    return batch_data_service_factory(kwargs).task


def file_client_factory(kwargs):
    return batch_data_service_factory(kwargs).file


def compute_node_client_factory(kwargs):
    return batch_data_service_factory(kwargs).compute_node


def batch_client_factory(**_):
    from azure.mgmt.batch import BatchManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    return get_mgmt_service_client(BatchManagementClient)


def batch_data_service_factory(kwargs):
    import azure.batch.batch_service_client as batch
    import azure.batch.batch_auth as batchauth

    account_name = kwargs.pop('account_name', None)
    account_key = kwargs.pop('account_key', None)
    account_endpoint = kwargs.pop('account_endpoint', None)
    kwargs.pop('yes', None)

    credentials = None
    if not account_key:
        from azure.cli.core._profile import Profile, CLOUD
        profile = Profile()
        credentials, _, _ = profile.get_login_credentials(
            resource=CLOUD.endpoints.batch_resource_id)
    else:
        credentials = batchauth.SharedKeyCredentials(account_name, account_key)
    return batch.BatchServiceClient(credentials, base_url=account_endpoint)
