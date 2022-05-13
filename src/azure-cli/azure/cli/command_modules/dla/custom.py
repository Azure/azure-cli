# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import time
import uuid

from knack.log import get_logger
from knack.prompting import prompt_pass, NoTTYException
from knack.util import CLIError

# pylint: disable=line-too-long
from azure.cli.core.commands.client_factory import get_mgmt_service_client

logger = get_logger(__name__)


# region account
def list_adla_account(client, resource_group_name=None):
    account_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(account_list)


def list_adla_jobs(client, account_name, top=500, name=None, submitter=None, submitted_after=None,
                   submitted_before=None, state=None, result=None, pipeline_id=None, recurrence_id=None):
    odata_filter_list = []
    if submitter:
        odata_filter_list.append("submitter eq '{}'".format(submitter))
    if name:
        odata_filter_list.append("name eq '{}'".format(name))
    if name:
        odata_filter_list.append("name eq '{}'".format(name))
    if state:
        odata_filter_list.append("({})".format(" or ".join(["state eq '{}'".format(f) for f in state])))
    if result:
        odata_filter_list.append("({})".format(" or ".join(["result eq '{}'".format(f) for f in result])))
    if submitted_after:
        odata_filter_list.append("submitTime ge datetimeoffset'{}'".format(submitted_after.isoformat()))
    if submitted_before:
        odata_filter_list.append("submitTime lt datetimeoffset'{}'".format(submitted_before.isoformat()))
    if pipeline_id:
        odata_filter_list.append("related/pipelineId eq guid'{}'".format(pipeline_id))
    if recurrence_id:
        odata_filter_list.append("related/recurrenceId eq guid'{}'".format(recurrence_id))

    filter_string = " and ".join(odata_filter_list)
    to_return = []

    job_list = client.list(account_name,
                           orderby="submitTime desc",
                           top=top if top <= 300 else None,
                           filter=filter_string if filter_string else None)
    if top <= 300:
        return job_list

    job_list = iter(job_list)
    for _ in range(top):
        elem = next(job_list, None)
        if elem:
            to_return.append(elem)
        else:
            break
    return to_return


def create_adla_account(cmd, client, resource_group_name, account_name, default_data_lake_store, location=None,
                        tags=None, max_degree_of_parallelism=30, max_job_count=3, query_store_retention=30, tier=None):
    from azure.mgmt.datalake.analytics.account.models import DataLakeAnalyticsAccount, DataLakeStoreAccountInfo
    adls_list = []
    adls_list.append(DataLakeStoreAccountInfo(default_data_lake_store))
    location = location or _get_resource_group_location(cmd.cli_ctx, resource_group_name)
    create_params = DataLakeAnalyticsAccount(location,
                                             default_data_lake_store,
                                             adls_list,
                                             tags=tags,
                                             max_degree_of_parallelism=max_degree_of_parallelism,
                                             max_job_count=max_job_count,
                                             query_store_retention=query_store_retention,
                                             new_tier=tier)

    return client.create(resource_group_name, account_name, create_params).result()


def update_adla_account(client, account_name, resource_group_name, tags=None, max_degree_of_parallelism=None,
                        max_job_count=None, query_store_retention=None, tier=None, firewall_state=None,
                        allow_azure_ips=None):
    from azure.mgmt.datalake.analytics.account.models import DataLakeAnalyticsAccountUpdateParameters
    update_params = DataLakeAnalyticsAccountUpdateParameters(
        tags=tags,
        max_degree_of_parallelism=max_degree_of_parallelism,
        max_job_count=max_job_count,
        query_store_retention=query_store_retention,
        new_tier=tier,
        firewall_state=firewall_state,
        firewall_allow_azure_ips=allow_azure_ips)

    return client.update(resource_group_name, account_name, update_params).result()
# endregion


# region storage
def add_adla_blob_storage(client, account_name, storage_account_name, access_key, resource_group_name, suffix=None):
    return client.add(resource_group_name,
                      account_name,
                      storage_account_name,
                      access_key,
                      suffix)


def update_adla_blob_storage(client, account_name, storage_account_name, access_key, resource_group_name, suffix=None):
    return client.update(resource_group_name,
                         account_name,
                         storage_account_name,
                         access_key,
                         suffix)
# endregion


# region firewall
def add_adla_firewall_rule(client, account_name, firewall_rule_name, start_ip_address, end_ip_address,
                           resource_group_name):
    from azure.mgmt.datalake.analytics.account.models import FirewallRule
    create_params = FirewallRule(start_ip_address, end_ip_address)
    return client.create_or_update(resource_group_name,
                                   account_name,
                                   firewall_rule_name,
                                   create_params)
# endregion


# region compute policy
def create_adla_compute_policy(client, account_name, compute_policy_name, object_id, object_type,
                               resource_group_name, max_dop_per_job=None, min_priority_per_job=None):
    from azure.mgmt.datalake.analytics.account.models import ComputePolicyCreateOrUpdateParameters
    if not max_dop_per_job and not min_priority_per_job:
        raise CLIError('Please specify at least one of --max-dop-per-job and --min-priority-per-job')

    create_params = ComputePolicyCreateOrUpdateParameters(object_id=object_id,
                                                          object_type=object_type)

    if max_dop_per_job:
        create_params.max_degree_of_parallelism_per_job = int(max_dop_per_job)

    if min_priority_per_job:
        create_params.min_priority_per_job = int(min_priority_per_job)

    return client.create_or_update(resource_group_name,
                                   account_name,
                                   compute_policy_name,
                                   create_params)


def update_adla_compute_policy(client, account_name, compute_policy_name, resource_group_name,
                               max_dop_per_job=None, min_priority_per_job=None):
    if not max_dop_per_job and not min_priority_per_job:
        raise CLIError('Please specify at least one of --max-dop-per-job and --min-priority-per-job')

    if max_dop_per_job:
        max_dop_per_job = int(max_dop_per_job)

    if min_priority_per_job:
        min_priority_per_job = int(min_priority_per_job)

    return client.update(resource_group_name,
                         account_name,
                         compute_policy_name,
                         max_dop_per_job,
                         min_priority_per_job)
# endregion


# region catalog
def create_adla_catalog_credential(client, account_name, database_name, credential_name, credential_user_name, uri,
                                   credential_user_password=None):
    from azure.mgmt.datalake.analytics.catalog.models import DataLakeAnalyticsCatalogCredentialCreateParameters
    if not credential_user_password:
        try:
            credential_user_password = prompt_pass('Password:', confirm=True)
        except NoTTYException:

            raise CLIError('Please specify both --user-name and --password in non-interactive mode.')

    create_params = DataLakeAnalyticsCatalogCredentialCreateParameters(credential_user_password,
                                                                       uri,
                                                                       credential_user_name)
    client.create_credential(account_name, database_name, credential_name, create_params)


def update_adla_catalog_credential(client, account_name, database_name, credential_name, credential_user_name, uri,
                                   credential_user_password=None, new_credential_user_password=None):
    from azure.mgmt.datalake.analytics.catalog.models import DataLakeAnalyticsCatalogCredentialUpdateParameters
    if not credential_user_password:
        try:
            credential_user_password = prompt_pass('Current Password:', confirm=True)
        except NoTTYException:

            raise CLIError('Please specify --user-name --password and --new-password in non-interactive mode.')

    if not new_credential_user_password:
        try:
            new_credential_user_password = prompt_pass('New Password:', confirm=True)
        except NoTTYException:

            raise CLIError('Please specify --user-name --password and --new-password in non-interactive mode.')

    update_params = DataLakeAnalyticsCatalogCredentialUpdateParameters(credential_user_password,
                                                                       new_credential_user_password,
                                                                       uri,
                                                                       credential_user_name)
    client.update_credential(account_name, database_name, credential_name, update_params)
# endregion


# region catalog lists
def list_catalog_tables(client, account_name, database_name, schema_name=None):
    if not schema_name:
        return client.list_tables_by_database(account_name, database_name)

    return client.list_tables(account_name, database_name, schema_name)


def list_catalog_views(client, account_name, database_name, schema_name=None):
    if not schema_name:
        return client.list_views_by_database(account_name, database_name)

    return client.list_views(account_name, database_name, schema_name)


def list_catalog_tvfs(client, account_name, database_name, schema_name=None):
    if not schema_name:
        return client.list_table_valued_functions_by_database(account_name, database_name)

    return client.list_table_valued_functions(account_name, database_name, schema_name)


def list_catalog_table_statistics(client, account_name, database_name, schema_name=None, table_name=None):
    if not schema_name and table_name:
        logger.warning('--table-name must be specified with --schema-name to be used. Defaulting to list all statistics in the database: %s', database_name)

    if not schema_name:
        return client.list_table_statistics_by_database(account_name, database_name)

    if not table_name:
        return client.list_table_statistics_by_database_and_schema(account_name, database_name, schema_name)

    return client.list_table_statistics(account_name, database_name, schema_name, table_name)
# endregion


# region job
def submit_adla_job(client, account_name, job_name, script, runtime_version=None, compile_mode=None, compile_only=False,
                    degree_of_parallelism=1, priority=1000, recurrence_id=None, recurrence_name=None, pipeline_id=None,
                    pipeline_name=None, pipeline_uri=None, run_id=None):
    from azure.mgmt.datalake.analytics.job.models import (
        JobType, CreateJobParameters, BuildJobParameters, CreateUSqlJobProperties, JobRelationshipProperties)

    if not script:
        # pylint: disable=line-too-long
        raise CLIError('Could not read script content from the supplied --script param. It is either empty or an invalid file')

    job_properties = CreateUSqlJobProperties(script)
    if runtime_version:
        job_properties.runtime_version = runtime_version

    if compile_mode:
        job_properties.compile_mode = compile_mode

    if compile_only:
        build_params = BuildJobParameters(JobType.usql,
                                          job_properties,
                                          job_name)

        return client.build(account_name, build_params)

    create_params = CreateJobParameters(JobType.usql,
                                        job_properties,
                                        job_name,
                                        degree_of_parallelism,
                                        priority)
    if recurrence_id:
        create_params.related = JobRelationshipProperties(recurrence_id,
                                                          pipeline_id,
                                                          pipeline_name,
                                                          pipeline_uri,
                                                          run_id,
                                                          recurrence_name)

    job_id = _get_uuid_str()

    return client.create(account_name, job_id, create_params)


def wait_adla_job(client, account_name, job_id, wait_interval_sec=5, max_wait_time_sec=-1):
    from azure.mgmt.datalake.analytics.job.models import JobState
    if wait_interval_sec < 1:
        raise CLIError('wait times must be greater than 0 when polling jobs. Value specified: {}'
                       .format(wait_interval_sec))

    job = client.get(account_name, job_id)
    time_waited_sec = 0
    while job.state != JobState.ended:
        if 0 < time_waited_sec >= max_wait_time_sec:
            # pylint: disable=line-too-long
            raise CLIError('Data Lake Analytics Job with ID: {0} has not completed in {1} seconds. Check job runtime or increase the value of --max-wait-time-sec'.format(job_id, time_waited_sec))
        logger.info('Job is not yet done. Current job state: \'%s\'', job.state)
        time.sleep(wait_interval_sec)
        job = client.get(account_name, job_id)

    return job
# endregion


# helpers
def _get_uuid_str():
    return str(uuid.uuid1())


def _get_resource_group_location(cli_ctx, resource_group_name):
    from azure.cli.core.profiles import ResourceType
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    # pylint: disable=no-member
    return client.resource_groups.get(resource_group_name).location
