# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
from urllib.parse import urlsplit
import configparser

from knack.log import get_logger

from msrest.exceptions import DeserializationError

from azure.mgmt.batch import BatchManagementClient
from azure.mgmt.batch.models import (BatchAccountCreateParameters, BatchAccountUpdateParameters,
                                     AutoStorageBaseProperties, ActivateApplicationPackageParameters,
                                     Application, EncryptionProperties,
                                     KeyVaultProperties, BatchAccountIdentity,
                                     BatchAccountRegenerateKeyParameters, PublicNetworkAccessType, BatchAccount,
                                     NetworkProfile, EndpointAccessProfile, IPRule, EndpointAccessDefaultAction,
                                     ResourceIdentityType, UserAssignedIdentities)
from azure.mgmt.batch.operations import (ApplicationPackageOperations)

from azure.batch.models import (CertificateAddParameter, PoolStopResizeOptions, PoolResizeParameter,
                                PoolResizeOptions, JobListOptions, JobListFromJobScheduleOptions,
                                TaskAddParameter, TaskAddCollectionParameter, TaskConstraints,
                                PoolUpdatePropertiesParameter, StartTask, AffinityInformation,
                                )

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import get_sdk, ResourceType
from azure.cli.core._profile import Profile
from azure.cli.core.util import sdk_no_wait, get_file_json, in_cloud_console

logger = get_logger(__name__)
MAX_TASKS_PER_REQUEST = 100


def transfer_doc(source_func, *additional_source_funcs):
    def _decorator(func):
        func.__doc__ = source_func.__doc__
        for f in additional_source_funcs:
            func.__doc__ += "\n" + f.__doc__
        return func

    return _decorator


# Mgmt custom commands
def list_accounts(client, resource_group_name=None):
    acct_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(acct_list)


def get_account(cmd, client, resource_group_name=None, account_name=None):
    if resource_group_name and account_name:
        return client.get(resource_group_name, account_name)
    try:
        account_endpoint = cmd.cli_ctx.config.get('batch', 'endpoint')
        if not account_endpoint:
            raise ValueError(
                "Missing required arguments. Either specify --resource-group-name and "
                "--account-name or must be logged into a batch account")
        account_list = list_accounts(client)
        for account in account_list:
            if account.account_endpoint in account_endpoint:
                return account
    except configparser.NoSectionError:
        raise ValueError(
            "Missing required arguments. Either specify --resource-group-name and "
            "--account-name or must be logged into a batch account")

    raise ValueError("Missing required arguments. Either specify --resource-group-name and "
                     "--account-name or must be logged into a batch account")


@transfer_doc(AutoStorageBaseProperties)
def create_account(client,
                   resource_group_name, account_name, location, tags=None, storage_account=None,
                   keyvault=None, keyvault_url=None, no_wait=False, public_network_access=None,
                   encryption_key_source=None, encryption_key_identifier=None,
                   mi_user_assigned=None, mi_system_assigned=None):
    properties = AutoStorageBaseProperties(storage_account_id=storage_account) \
        if storage_account else None

    identity = None
    if mi_system_assigned:
        identity = BatchAccountIdentity(type=ResourceIdentityType.SYSTEM_ASSIGNED)

    if mi_user_assigned:
        useridentity = UserAssignedIdentities()
        my_dict = {mi_user_assigned: useridentity}
        identity = BatchAccountIdentity(type=ResourceIdentityType.USER_ASSIGNED, user_assigned_identities=my_dict)

    if (encryption_key_source and
            encryption_key_source.lower() == "microsoft.keyvault" and not encryption_key_identifier):
        raise ValueError("The --encryption-key-identifier property is required when "
                         "--encryption-key-source is set to Microsoft.KeyVault")
    encryption_key_identifier = KeyVaultProperties(key_identifier=encryption_key_identifier) \
        if encryption_key_identifier else None
    encryption = EncryptionProperties(
        key_source=encryption_key_source,
        encryption_key_identifier=encryption_key_identifier) if encryption_key_source else None
    parameters = BatchAccountCreateParameters(location=location,
                                              tags=tags,
                                              auto_storage=properties,
                                              public_network_access=public_network_access,
                                              encryption=encryption,
                                              identity=identity)
    if keyvault:
        parameters.key_vault_reference = {'id': keyvault, 'url': keyvault_url}
        parameters.pool_allocation_mode = 'UserSubscription'

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name=resource_group_name,
                       account_name=account_name, parameters=parameters)


@transfer_doc(AutoStorageBaseProperties)
def update_account(client, resource_group_name, account_name,
                   tags=None, storage_account=None, encryption_key_source=None, public_network_access=None,
                   encryption_key_identifier=None, mi_user_assigned=None, mi_system_assigned=None):

    properties = AutoStorageBaseProperties(storage_account_id=storage_account) \
        if storage_account else None
    if (encryption_key_source and
            encryption_key_source.lower() == "microsoft.keyvault" and not
            encryption_key_identifier):
        raise ValueError("The --encryption-key-identifier property is required when "
                         "--encryption-key-source is set to Microsoft.KeyVault")
    encryption_key_identifier = KeyVaultProperties(key_identifier=encryption_key_identifier) \
        if encryption_key_identifier else None
    encryption = EncryptionProperties(
        key_source=encryption_key_source,
        encryption_key_identifier=encryption_key_identifier) if encryption_key_source else None

    identity = None
    if mi_system_assigned:
        identity = BatchAccountIdentity(type=ResourceIdentityType.SYSTEM_ASSIGNED)

    if mi_user_assigned:
        useridentity = UserAssignedIdentities()
        my_dict = {mi_user_assigned: useridentity}
        identity = BatchAccountIdentity(type=ResourceIdentityType.USER_ASSIGNED, user_assigned_identities=my_dict)

    parameters = BatchAccountUpdateParameters(
        tags=tags,
        encryption=encryption,
        identity=identity,
        public_network_access=public_network_access,
        auto_storage=properties)

    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         parameters=parameters)


def assign_batch_identity(cmd, client, resource_group_name, account_name, mi_system_assigned=None,
                          mi_user_assigned=None):
    update_account(client=client, resource_group_name=resource_group_name, account_name=account_name,
                   mi_system_assigned=mi_system_assigned, mi_user_assigned=mi_user_assigned)
    return show_batch_identity(cmd=cmd, client=client, resource_group_name=resource_group_name,
                               account_name=account_name)


def remove_batch_identity(cmd, client, resource_group_name, account_name, mi_system_assigned=None,
                          mi_user_assigned=None):
    batch_account: BatchAccount = get_account(cmd, client, resource_group_name, account_name)

    if batch_account is None or batch_account.identity is None:
        return None

    if mi_system_assigned:
        batch_account.identity.type = (ResourceIdentityType.NONE
                                       if batch_account.identity.type == ResourceIdentityType.SYSTEM_ASSIGNED
                                       else ResourceIdentityType.USER_ASSIGNED)
    # batch only supports 1 managed user id
    if mi_user_assigned and batch_account.identity.user_assigned_identities:
        keyslist = list(batch_account.identity.user_assigned_identities.keys())
        if keyslist and mi_user_assigned == keyslist[0]:
            batch_account.identity.user_assigned_identities = None
            batch_account.identity.type = (ResourceIdentityType.NONE
                                           if batch_account.identity.type == ResourceIdentityType.USER_ASSIGNED
                                           else ResourceIdentityType.SYSTEM_ASSIGNED)

    parameters = BatchAccountUpdateParameters(identity=batch_account.identity)

    client.update(resource_group_name=resource_group_name, account_name=account_name, parameters=parameters)

    return show_batch_identity(cmd=cmd, client=client, resource_group_name=resource_group_name,
                               account_name=account_name)


def show_batch_identity(cmd, client, resource_group_name, account_name):
    batch_account: BatchAccount = get_account(cmd, client, resource_group_name, account_name)

    return batch_account.identity


# pylint: disable=inconsistent-return-statements
def login_account(cmd, client, resource_group_name, account_name, shared_key_auth=False, show=False):
    account = client.get(resource_group_name=resource_group_name,
                         account_name=account_name)
    cmd.cli_ctx.config.set_value('batch', 'account', account.name)
    cmd.cli_ctx.config.set_value('batch', 'endpoint',
                                 f'https://{account.account_endpoint}/')

    if shared_key_auth:
        keys = client.get_keys(resource_group_name=resource_group_name,
                               account_name=account_name)
        cmd.cli_ctx.config.set_value('batch', 'auth_mode', 'shared_key')
        cmd.cli_ctx.config.set_value('batch', 'access_key', keys.primary)
        if show:
            return {
                'account': account.name,
                'endpoint': f'https://{account.account_endpoint}/',
                'primaryKey': keys.primary,
                'secondaryKey': keys.secondary
            }
    else:
        cmd.cli_ctx.config.set_value('batch', 'auth_mode', 'aad')
        if show:
            if in_cloud_console():
                resource = cmd.cli_ctx.cloud.endpoints.active_directory_resource_id
            else:
                resource = cmd.cli_ctx.cloud.endpoints.batch_resource_id
            profile = Profile(cli_ctx=cmd.cli_ctx)
            creds, subscription, tenant = profile.get_raw_token(resource=resource)
            return {
                'account': account.name,
                'endpoint': f'https://{account.account_endpoint}/',
                'tokenType': creds[0],
                'accessToken': creds[1],
                'expiresOn': creds[2]['expiresOn'],
                'subscription': subscription,
                'tenant': tenant,
                'resource': resource
            }


def renew_accounts_keys(client, resource_group_name, account_name, key_name=None):

    parameters = BatchAccountRegenerateKeyParameters(key_name=key_name)

    return client.regenerate_key(resource_group_name=resource_group_name,
                                 account_name=account_name, parameters=parameters)


def get_network_profile(cmd, client, resource_group_name=None, account_name=None):

    batch_account: BatchAccount = get_account(cmd, client, resource_group_name, account_name)

    return batch_account.network_profile


def update_network_profile(cmd, client, resource_group_name=None, account_name=None,
                           profile=None, default_action=None):

    batch_account: BatchAccount = get_account(cmd, client, resource_group_name, account_name)

    # we want to use the existing network_profile if it exists
    networkprofile = batch_account.network_profile
    if networkprofile is None:
        networkprofile = NetworkProfile()

    if profile.lower() == "batchaccount":
        if networkprofile.account_access is None:
            networkprofile.account_access = EndpointAccessProfile(default_action=default_action)

        networkprofile.account_access.default_action = default_action

    if profile.lower() == "nodemanagement":
        if networkprofile.node_management_access is None:
            networkprofile.node_management_access = EndpointAccessProfile(default_action=default_action)

        networkprofile.node_management_access.default_action = default_action

    parameters = BatchAccountUpdateParameters(network_profile=networkprofile)

    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         parameters=parameters)


def list_network_rules(cmd, client, resource_group_name=None, account_name=None):
    batch_account: BatchAccount = get_account(cmd, client, resource_group_name, account_name)

    return batch_account.network_profile


def add_network_rule(cmd, client, resource_group_name=None, account_name=None, profile=None, ip_address=None):
    batch_account: BatchAccount = get_account(cmd, client, resource_group_name, account_name)

    # we want to use the existing network_profile if it exists, else build one up
    networkprofile = batch_account.network_profile
    if networkprofile is None:
        networkprofile = NetworkProfile()

    if profile.lower() == "batchaccount":
        if networkprofile.account_access is None:
            networkprofile.account_access = EndpointAccessProfile(
                default_action=EndpointAccessDefaultAction.ALLOW)
        if networkprofile.account_access.ip_rules is None:
            networkprofile.account_access.ip_rules = []
        networkprofile.account_access.ip_rules.append(IPRule(value=ip_address))

    if profile.lower() == "nodemanagement":
        if networkprofile.node_management_access is None:
            networkprofile.node_management_access = EndpointAccessProfile(
                default_action=EndpointAccessDefaultAction.ALLOW)
        if networkprofile.node_management_access.ip_rules is None:
            networkprofile.node_management_access.ip_rules = []
        networkprofile.node_management_access.ip_rules.append(IPRule(value=ip_address))

    # Not sure if i want to enable public_network_access as part of this
    parameters = BatchAccountUpdateParameters(public_network_access=PublicNetworkAccessType.ENABLED,
                                              network_profile=networkprofile)

    client.update(resource_group_name=resource_group_name,
                  account_name=account_name,
                  parameters=parameters)

    return list_network_rules(cmd, client, resource_group_name, account_name)


def delete_network_rule(cmd, client, resource_group_name=None, account_name=None, profile=None, ip_address=None):
    batch_account: BatchAccount = get_account(cmd, client, resource_group_name, account_name)

    # we want to use the existing network_profile if it exists, else build one up
    networkprofile = batch_account.network_profile
    if networkprofile is None:
        networkprofile = NetworkProfile()

    if profile.lower() == "batchaccount":
        if networkprofile.account_access is None:
            networkprofile.account_access = EndpointAccessProfile(
                default_action=EndpointAccessDefaultAction.ALLOW)
        if networkprofile.account_access.ip_rules is None:
            networkprofile.account_access.ip_rules = []

        for iprule in networkprofile.account_access.ip_rules:
            if iprule.value == ip_address:
                networkprofile.account_access.ip_rules.remove(iprule)

    if profile.lower() == "nodemanagement":
        if networkprofile.node_management_access is None:
            networkprofile.node_management_access = EndpointAccessProfile(
                default_action=EndpointAccessDefaultAction.ALLOW)
        if networkprofile.node_management_access.ip_rules is None:
            networkprofile.node_management_access.ip_rules = []
        for iprule in networkprofile.node_management_access.ip_rules:
            if iprule.value == ip_address:
                networkprofile.node_management_access.ip_rules.remove(iprule)

    # Not sure if i want to enable public_network_access as part of this
    parameters = BatchAccountUpdateParameters(public_network_access=PublicNetworkAccessType.ENABLED,
                                              network_profile=networkprofile)

    client.update(resource_group_name=resource_group_name,
                  account_name=account_name,
                  parameters=parameters)

    return list_network_rules(cmd, client, resource_group_name, account_name)


@transfer_doc(Application)
def update_application(client,
                       resource_group_name, account_name, application_name, allow_updates=None,
                       display_name=None, default_version=None):
    parameters = Application(
        allow_updates=allow_updates,
        display_name=display_name,
        default_version=default_version)
    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         application_name=application_name,
                         parameters=parameters)


def _upload_package_blob(ctx, package_file, url):
    """Upload the location file to storage url provided by autostorage"""
    BlockBlobService = get_sdk(ctx, ResourceType.DATA_STORAGE, 'blob#BlockBlobService')

    uri = urlsplit(url)
    # in uri path, it always start with '/', so container name is at second block
    pathParts = uri.path.split('/', 2)
    container_name = pathParts[1]
    blob_name = pathParts[2]
    # we need handle the scenario storage account not in public Azure
    hostParts = uri.netloc.split('.', 2)
    account_name = hostParts[0]
    # endpoint suffix needs to ignore the 'blob' part in the host name
    endpoint_suffix = hostParts[2]

    sas_service = BlockBlobService(account_name=account_name,
                                   sas_token=uri.query,
                                   endpoint_suffix=endpoint_suffix)
    sas_service.create_blob_from_path(
        container_name=container_name,
        blob_name=blob_name,
        file_path=package_file,
    )


@transfer_doc(ApplicationPackageOperations.create)
def create_application_package(cmd, client,
                               resource_group_name, account_name, application_name, version_name,
                               package_file):
    # create application if not exist
    mgmt_client = get_mgmt_service_client(cmd.cli_ctx, BatchManagementClient)
    try:
        mgmt_client.application.get(resource_group_name, account_name, application_name)
    except Exception:  # pylint:disable=broad-except
        mgmt_client.application.create(resource_group_name, account_name, application_name)

    result = client.create(resource_group_name, account_name, application_name, version_name)

    # upload binary as application package
    logger.info('Uploading %s to storage blob %s...', package_file, result.storage_url)
    _upload_package_blob(cmd.cli_ctx, package_file, result.storage_url)

    # activate the application package
    parameters = ActivateApplicationPackageParameters(format="zip")
    client.activate(resource_group_name, account_name, application_name, version_name, parameters)
    return client.get(resource_group_name, account_name, application_name, version_name)


@transfer_doc(ApplicationPackageOperations.activate)
def activate_application_package(client, resource_group_name, account_name, application_name, version_name, f_ormat):
    # activate the application package
    parameters = ActivateApplicationPackageParameters(format=f_ormat)
    return client.activate(resource_group_name, account_name, application_name, version_name, parameters)


# Data plane custom commands


@transfer_doc(CertificateAddParameter)
def create_certificate(client, certificate_file, thumbprint, password=None):
    thumbprint_algorithm = 'sha1'
    certificate_format = 'pfx' if password or certificate_file.endswith('.pfx') else 'cer'
    with open(certificate_file, "rb") as f:
        data_bytes = f.read()
    data = base64.b64encode(data_bytes).decode('utf-8')
    cert = CertificateAddParameter(
        thumbprint=thumbprint,
        thumbprint_algorithm=thumbprint_algorithm,
        data=data,
        certificate_format=certificate_format,
        password=password)
    client.add(cert)
    return client.get(thumbprint_algorithm, thumbprint)


def delete_certificate(client, thumbprint, abort=False):
    thumbprint_algorithm = 'sha1'
    if abort:
        return client.cancel_deletion(thumbprint_algorithm, thumbprint)
    return client.delete(thumbprint_algorithm, thumbprint)


@transfer_doc(PoolResizeParameter)
def resize_pool(client, pool_id, target_dedicated_nodes=None, target_low_priority_nodes=None,
                resize_timeout=None, node_deallocation_option=None,
                if_match=None, if_none_match=None, if_modified_since=None,
                if_unmodified_since=None, abort=False):
    if abort:
        stop_resize_option = PoolStopResizeOptions(if_match=if_match,
                                                   if_none_match=if_none_match,
                                                   if_modified_since=if_modified_since,
                                                   if_unmodified_since=if_unmodified_since)
        return client.stop_resize(pool_id, pool_stop_resize_options=stop_resize_option)

    param = PoolResizeParameter(target_dedicated_nodes=target_dedicated_nodes,
                                target_low_priority_nodes=target_low_priority_nodes,
                                resize_timeout=resize_timeout,
                                node_deallocation_option=node_deallocation_option)
    resize_option = PoolResizeOptions(if_match=if_match,
                                      if_none_match=if_none_match,
                                      if_modified_since=if_modified_since,
                                      if_unmodified_since=if_unmodified_since)
    return client.resize(pool_id, param, pool_resize_options=resize_option)


@transfer_doc(PoolUpdatePropertiesParameter, StartTask)
def update_pool(client,
                pool_id, json_file=None, start_task_command_line=None, certificate_references=None,
                application_package_references=None, metadata=None,
                start_task_environment_settings=None, start_task_wait_for_success=None,
                start_task_max_task_retry_count=None):
    if json_file:
        json_obj = get_file_json(json_file)
        param = None
        try:
            param = PoolUpdatePropertiesParameter.from_dict(json_obj)
        except DeserializationError:
            pass
        if not param:
            raise ValueError(f"JSON file '{json_file}' is not in correct format.")

        if param.certificate_references is None:
            param.certificate_references = []
        if param.metadata is None:
            param.metadata = []
        if param.application_package_references is None:
            param.application_package_references = []
    else:
        if certificate_references is None:
            certificate_references = []
        if metadata is None:
            metadata = []
        if application_package_references is None:
            application_package_references = []
        param = PoolUpdatePropertiesParameter(
            certificate_references=certificate_references,
            application_package_references=application_package_references,
            metadata=metadata)

        if start_task_command_line:
            param.start_task = StartTask(command_line=start_task_command_line,
                                         environment_settings=start_task_environment_settings,
                                         wait_for_success=start_task_wait_for_success,
                                         max_task_retry_count=start_task_max_task_retry_count)
    client.update_properties(pool_id=pool_id, pool_update_properties_parameter=param)
    return client.get(pool_id)


def list_job(client, job_schedule_id=None, filter=None,  # pylint: disable=redefined-builtin
             select=None, expand=None):
    if job_schedule_id:
        option1 = JobListFromJobScheduleOptions(filter=filter,
                                                select=select,
                                                expand=expand)
        return list(client.list_from_job_schedule(job_schedule_id=job_schedule_id,
                                                  job_list_from_job_schedule_options=option1))
    option2 = JobListOptions(filter=filter,
                             select=select,
                             expand=expand)
    return list(client.list(job_list_options=option2))


@transfer_doc(TaskAddParameter, TaskConstraints, AffinityInformation)
def create_task(client,
                job_id, json_file=None, task_id=None, command_line=None, resource_files=None,
                environment_settings=None, affinity_id=None, max_wall_clock_time=None,
                retention_time=None, max_task_retry_count=None,
                application_package_references=None):
    task = None
    tasks = []
    if json_file:
        json_obj = get_file_json(json_file)
        try:
            task = TaskAddParameter.from_dict(json_obj)
        except (DeserializationError, TypeError):
            try:
                task_collection = TaskAddCollectionParameter.from_dict(json_obj)
                tasks = task_collection.value
            except (DeserializationError, TypeError):
                try:
                    for json_task in json_obj:
                        tasks.append(TaskAddParameter.from_dict(json_task))
                except (DeserializationError, TypeError):
                    raise ValueError(f"JSON file '{json_file}' is not formatted correctly.")
    else:
        if command_line is None or task_id is None:
            raise ValueError("Missing required arguments.\nEither --json-file, "
                             "or both --task-id and --command-line must be specified.")
        task = TaskAddParameter(
            id=task_id,
            command_line=command_line,
            resource_files=resource_files,
            environment_settings=environment_settings,
            affinity_info=AffinityInformation(affinity_id=affinity_id) if affinity_id else None,
            application_package_references=application_package_references)
        if max_wall_clock_time is not None or retention_time is not None \
                or max_task_retry_count is not None:
            task.constraints = TaskConstraints(max_wall_clock_time=max_wall_clock_time,
                                               retention_time=retention_time,
                                               max_task_retry_count=max_task_retry_count)
    if task is not None:
        client.add(job_id=job_id, task=task)
        return client.get(job_id=job_id, task_id=task.id)

    submitted_tasks = []
    for i in range(0, len(tasks), MAX_TASKS_PER_REQUEST):
        submission = client.add_collection(
            job_id=job_id,
            value=tasks[i:i + MAX_TASKS_PER_REQUEST])
        submitted_tasks.extend(submission.value)  # pylint: disable=no-member
    return submitted_tasks
