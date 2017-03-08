# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------




import time
import uuid

from azure.cli.core.prompting import prompt_pass, NoTTYException
from azure.mgmt.datalake.analytics.account.models import (DataLakeAnalyticsAccountUpdateParameters,
                                                          FirewallRule,
                                                          DataLakeAnalyticsAccount,
                                                          DataLakeStoreAccountInfo)

from azure.mgmt.datalake.analytics.job.models import (JobType,
                                                      JobState,
                                                      JobInformation,
                                                      USqlJobProperties)
# pylint: disable=line-too-long
from azure.mgmt.datalake.analytics.catalog.models import (DataLakeAnalyticsCatalogCredentialCreateParameters,
                                                          DataLakeAnalyticsCatalogCredentialUpdateParameters)
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core._util import CLIError
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)
# account customiaztions
def list_adla_account(client, resource_group_name=None):
    account_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(account_list)

# pylint: disable=too-many-arguments
def create_adla_account(client,
                        resource_group_name,
                        account_name,
                        default_datalake_store,
                        location=None,
                        tags=None,
                        max_degree_of_parallelism=30,
                        max_job_count=3,
                        query_store_retention=30,
                        tier=None):
    adls_list = list()
    adls_list.append(DataLakeStoreAccountInfo(default_datalake_store))
    location = location or get_resource_group_location(resource_group_name)
    create_params = DataLakeAnalyticsAccount(location,
                                             default_datalake_store,
                                             adls_list)
    if tags:
        create_params.tags = tags

    if max_degree_of_parallelism:
        create_params.max_degree_of_parallelism = max_degree_of_parallelism

    if max_job_count:
        create_params.max_job_count = max_job_count

    if query_store_retention:
        create_params.query_store_retention = query_store_retention

    if tier:
        create_params.new_tier = tier

    return client.create(resource_group_name, account_name, create_params)

# pylint: disable=too-many-arguments
def update_adla_account(client,
                        account_name,
                        tags=None,
                        resource_group_name=None,
                        max_degree_of_parallelism=None,
                        max_job_count=None,
                        query_store_retention=None,
                        tier=None,
                        firewall_state=None,
                        allow_azure_ips=None):
    if not resource_group_name:
        resource_group_name = _get_resource_group_by_account_name(client, account_name)

    update_params = DataLakeAnalyticsAccountUpdateParameters(
        tags=tags,
        max_degree_of_parallelism=max_degree_of_parallelism,
        max_job_count=max_job_count,
        query_store_retention=query_store_retention,
        new_tier=tier,
        firewall_state=firewall_state,
        firewall_allow_azure_ips=allow_azure_ips)

    return client.update(resource_group_name, account_name, update_params)

# firewall customizations
# pylint: disable=too-many-arguments
def add_adla_firewall_rule(client,
                           account_name,
                           firewall_rule_name,
                           start_ip_address,
                           end_ip_address,
                           resource_group_name=None):
    if not resource_group_name:
        resource_group_name = _get_resource_group_by_account_name(client, account_name)

    create_params = FirewallRule(start_ip_address, end_ip_address)
    return client.create_or_update(resource_group_name,
                                   account_name,
                                   firewall_rule_name,
                                   create_params)

# catalog customizations
# pylint: disable=too-many-arguments
def create_adla_catalog_credential(client,
                                   account_name,
                                   database_name,
                                   credential_name,
                                   credential_user_name,
                                   uri,
                                   credential_user_password=None):

    if not credential_user_password:
        try:
            credential_user_password = prompt_pass('Credential Password:')
        except NoTTYException:
            # pylint: disable=line-too-long
            raise CLIError('Please specify both --credential-user-name and --password in non-interactive mode.')

    create_params = DataLakeAnalyticsCatalogCredentialCreateParameters(credential_user_password,
                                                                       uri,
                                                                       credential_user_name)
    client.create_credential(account_name, database_name, credential_name, create_params)

# pylint: disable=too-many-arguments
def update_adla_catalog_credential(client,
                                   account_name,
                                   database_name,
                                   credential_name,
                                   credential_user_name,
                                   uri,
                                   credential_user_password=None,
                                   new_credential_user_password=None):
    if not credential_user_password:
        try:
            credential_user_password = prompt_pass('Current Credential Password:')
        except NoTTYException:
            # pylint: disable=line-too-long
            raise CLIError('Please specify --credential-user-name --password and --new-password in non-interactive mode.')

    if not new_credential_user_password:
        try:
            new_credential_user_password = prompt_pass('New Credential Password:')
        except NoTTYException:
            # pylint: disable=line-too-long
            raise CLIError('Please specify --credential-user-name --password and --new-password in non-interactive mode.')

    update_params = DataLakeAnalyticsCatalogCredentialUpdateParameters(credential_user_password,
                                                                       new_credential_user_password,
                                                                       uri,
                                                                       credential_user_name)
    client.update_credential(account_name, database_name, credential_name, update_params)

# job customizations
# pylint: disable=too-many-arguments
def submit_adla_job(client,
                    account_name,
                    job_name,
                    script,
                    runtime_version=None,
                    compile_mode=None,
                    compile_only=False,
                    degree_of_parallelism=1,
                    priority=1000):
    contents = None
    # script can be either script contents or a path to a script
    # we attempt to always open the script path first, if that fails
    # then treat it as contents
    try:
        with open(script, 'r') as f:
            contents = f.read()
    #pylint: disable=broad-except
    except Exception:
        contents = script

    if not contents:
        # pylint: disable=line-too-long
        raise CLIError('Could not read script content from the supplied --script param. It is either empty or an invalid file. value: {}'.format(script))

    job_properties = USqlJobProperties(contents)
    if runtime_version:
        job_properties.runtime_version = runtime_version

    if compile_mode:
        job_properties.compile_mode = compile_mode

    submit_params = JobInformation(job_name,
                                   JobType.usql,
                                   job_properties,
                                   degree_of_parallelism,
                                   priority)
    if compile_only:
        return client.build(account_name, submit_params)

    job_id = _get_uuid_str()

    return client.create(account_name, job_id, submit_params)

def wait_adla_job(client,
                  account_name,
                  job_id,
                  wait_interval_sec=5,
                  max_wait_time_sec=-1):
    if wait_interval_sec < 1:
        # pylint: disable=line-too-long
        logger.warning('wait times must be positive when polling jobs, setting to the default value of 5 seconds')
        wait_interval_sec = 5

    job = client.get(account_name, job_id)
    time_waited_sec = 0
    while job.state != JobState.ended:
        if max_wait_time_sec > 0 and time_waited_sec >= max_wait_time_sec:
            # pylint: disable=line-too-long
            raise CLIError('Data Lake Analytics Job with ID: {0} has not completed in {1} seconds. Check job runtime or increase the value of --max-wait-time-sec'.format(job_id, time_waited_sec))
        print('Job is not yet done. Current job state: \'{0}\''.format(job.state))
        time.sleep(wait_interval_sec)
        job = client.get(account_name, job_id)

    return job

# helpers
def _get_uuid_str():
    return str(uuid.uuid1())

def _get_resource_group_by_account_name(client, account_name):
    accts = list_adla_account(client)
    for item in accts:
        if item.name.lower() == account_name.lower():
            item_id = item.id
            rg_start = item_id.lower().index('resourcegroups/') + len('resourcegroups/')
            rg_length = item_id.lower().index('/providers/') - rg_start
            return item_id[rg_start:rg_length + rg_start]

    raise CLIError(
        # pylint: disable=line-too-long
        'Could not find account: \'{}\' in any resource group in the currently selected subscription: {}. Please ensure this account exists and that the current user has access to it.'
        .format(account_name, client.subscription_id))

def get_resource_group_location(resource_group_name):
    from azure.mgmt.resource.resources import ResourceManagementClient
    client = get_mgmt_service_client(ResourceManagementClient)
    # pylint: disable=no-member
    return client.resource_groups.get(resource_group_name).location
