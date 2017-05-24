# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import base64
from six.moves.urllib.parse import urlsplit  # pylint: disable=import-error

from msrest.exceptions import DeserializationError, ValidationError, ClientRequestError
from azure.mgmt.batch import BatchManagementClient
from azure.mgmt.batch.models import (BatchAccountCreateParameters,
                                     AutoStorageBaseProperties,
                                     ApplicationUpdateParameters)
from azure.mgmt.batch.operations import (ApplicationPackageOperations)

from azure.batch.models import (CertificateAddParameter, PoolStopResizeOptions, PoolResizeParameter,
                                PoolResizeOptions, JobListOptions, JobListFromJobScheduleOptions,
                                TaskAddParameter, TaskConstraints, PoolUpdatePropertiesParameter,
                                StartTask, BatchErrorException)

from azure.cli.core.util import CLIError
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import get_sdk, ResourceType
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)


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


@transfer_doc(AutoStorageBaseProperties)
def create_account(client,
                   resource_group_name, account_name, location, tags=None, storage_account=None,
                   keyvault=None, keyvault_url=None):
    properties = AutoStorageBaseProperties(storage_account_id=storage_account) \
        if storage_account else None
    parameters = BatchAccountCreateParameters(location=location,
                                              tags=tags,
                                              auto_storage=properties)
    if keyvault:
        parameters.key_vault_reference = {'id': keyvault, 'url': keyvault_url}
        parameters.pool_allocation_mode = 'UserSubscription'

    return client.create(resource_group_name=resource_group_name,
                         account_name=account_name,
                         parameters=parameters)


@transfer_doc(AutoStorageBaseProperties)
def update_account(client, resource_group_name, account_name,
                   tags=None, storage_account=None):
    properties = AutoStorageBaseProperties(storage_account_id=storage_account) \
        if storage_account else None
    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         tags=tags,
                         auto_storage=properties)


def login_account(client, resource_group_name, account_name, shared_key_auth=False):
    from azure.cli.core._config import az_config, set_global_config

    account = client.get(resource_group_name=resource_group_name,
                         account_name=account_name)
    if not az_config.config_parser.has_section('batch'):
        az_config.config_parser.add_section('batch')
    az_config.config_parser.set('batch', 'account', account.name)
    az_config.config_parser.set('batch', 'endpoint',
                                'https://{}/'.format(account.account_endpoint))

    if shared_key_auth:
        keys = client.get_keys(resource_group_name=resource_group_name,
                               account_name=account_name)
        az_config.config_parser.set('batch', 'auth_mode', 'shared_key')
        az_config.config_parser.set('batch', 'access_key', keys.primary)
    else:
        az_config.config_parser.set('batch', 'auth_mode', 'aad')
        az_config.config_parser.remove_option('batch', 'access_key')

    set_global_config(az_config.config_parser)


@transfer_doc(ApplicationUpdateParameters)
def update_application(client,
                       resource_group_name, account_name, application_id, allow_updates=None,
                       display_name=None, default_version=None):
    parameters = ApplicationUpdateParameters(allow_updates=allow_updates,
                                             display_name=display_name,
                                             default_version=default_version)
    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         application_id=application_id,
                         parameters=parameters)


def _upload_package_blob(package_file, url):
    """Upload the location file to storage url provided by autostorage"""
    BlockBlobService = get_sdk(ResourceType.DATA_STORAGE, 'blob#BlockBlobService')

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
def create_application_package(client,
                               resource_group_name, account_name, application_id, version,
                               package_file):
    # create application if not exist
    mgmt_client = get_mgmt_service_client(BatchManagementClient)
    try:
        mgmt_client.application.get(resource_group_name, account_name, application_id)
    except Exception:  # pylint:disable=broad-except
        mgmt_client.application.create(resource_group_name, account_name, application_id)

    result = client.create(resource_group_name, account_name, application_id, version)

    # upload binary as application package
    logger.info('Uploading %s to storage blob %s...', package_file, result.storage_url)
    _upload_package_blob(package_file, result.storage_url)

    # activate the application package
    client.activate(resource_group_name, account_name, application_id, version, "zip")
    return client.get(resource_group_name, account_name, application_id, version)


# Data plane custom commands

def _handle_batch_exception(action):
    try:
        return action()
    except BatchErrorException as ex:
        try:
            message = ex.error.message.value
            if ex.error.values:
                for detail in ex.error.values:
                    message += "\n{}: {}".format(detail.key, detail.value)
            raise CLIError(message)
        except AttributeError:
            raise CLIError(ex)
    except (ValidationError, ClientRequestError) as ex:
        raise CLIError(ex)


@transfer_doc(CertificateAddParameter)
def create_certificate(client, certificate_file, thumbprint, password=None):
    thumbprint_algorithm = 'sha1'

    def action():
        client.add(cert)
        return client.get(thumbprint_algorithm, thumbprint)

    certificate_format = 'pfx' if password else 'cer'
    with open(certificate_file, "rb") as f:
        data_bytes = f.read()
    data = base64.b64encode(data_bytes).decode('utf-8')
    cert = CertificateAddParameter(thumbprint, thumbprint_algorithm, data,
                                   certificate_format=certificate_format,
                                   password=password)
    return _handle_batch_exception(action)


def delete_certificate(client, thumbprint, abort=False):
    thumbprint_algorithm = 'sha1'

    def action():
        if abort:
            client.cancel_deletion(thumbprint_algorithm, thumbprint)
        else:
            client.delete(thumbprint_algorithm, thumbprint)

    return _handle_batch_exception(action)


@transfer_doc(PoolResizeParameter)
def resize_pool(client, pool_id, target_dedicated_nodes=None, target_low_priority_nodes=None,
                resize_timeout=None, node_deallocation_option=None,
                if_match=None, if_none_match=None, if_modified_since=None,
                if_unmodified_since=None, abort=False):
    def action():
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

    return _handle_batch_exception(action)


@transfer_doc(PoolUpdatePropertiesParameter, StartTask)
def update_pool(client,
                pool_id, json_file=None, start_task_command_line=None, certificate_references=None,
                application_package_references=None, metadata=None,
                start_task_environment_settings=None, start_task_wait_for_success=None,
                start_task_max_task_retry_count=None):
    def action():
        client.update_properties(pool_id=pool_id, pool_update_properties_parameter=param)
        return client.get(pool_id)

    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            param = None
            try:
                param = client._deserialize(  # pylint: disable=protected-access
                    'PoolUpdatePropertiesParameter', json_obj)
            except DeserializationError:
                pass
            if not param:
                raise ValueError("JSON file '{}' is not in correct format.".format(json_file))

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
        param = PoolUpdatePropertiesParameter(certificate_references,
                                              application_package_references,
                                              metadata)

        if start_task_command_line:
            param.start_task = StartTask(start_task_command_line,
                                         environment_settings=start_task_environment_settings,
                                         wait_for_success=start_task_wait_for_success,
                                         max_task_retry_count=start_task_max_task_retry_count)
    return _handle_batch_exception(action)


def list_job(client, job_schedule_id=None, filter=None,  # pylint: disable=redefined-builtin
             select=None, expand=None):
    def action():
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

    return _handle_batch_exception(action)


@transfer_doc(TaskAddParameter, TaskConstraints)
def create_task(client,
                job_id, json_file=None, task_id=None, command_line=None, resource_files=None,
                environment_settings=None, affinity_info=None, max_wall_clock_time=None,
                retention_time=None, max_task_retry_count=None,
                application_package_references=None):
    def action():
        if task is not None:
            client.add(job_id=job_id, task=task)
            return client.get(job_id=job_id, task_id=task.id)

        result = client.add_collection(job_id=job_id, value=tasks)
        return result.value

    task = None
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            try:
                task = client._deserialize(  # pylint: disable=protected-access
                    'TaskAddParameter', json_obj)
            except DeserializationError:
                try:
                    tasks = client._deserialize(  # pylint: disable=protected-access
                        '[TaskAddParameter]', json_obj)
                except DeserializationError:
                    raise ValueError("JSON file '{}' is not in reqired format.".format(json_file))
    else:
        if command_line is None or task_id is None:
            raise ValueError("Missing required arguments.\nEither --json-file, "
                             "or both --task-id and --command-line must be specified.")
        task = TaskAddParameter(task_id, command_line,
                                resource_files=resource_files,
                                environment_settings=environment_settings,
                                affinity_info=affinity_info,
                                application_package_references=application_package_references)
        if max_wall_clock_time is not None or retention_time is not None \
                or max_task_retry_count is not None:
            task.constraints = TaskConstraints(max_wall_clock_time=max_wall_clock_time,
                                               retention_time=retention_time,
                                               max_task_retry_count=max_task_retry_count)
    return _handle_batch_exception(action)
