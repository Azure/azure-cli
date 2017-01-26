# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit # pylint: disable=import-error
import json
import base64

from msrest.exceptions import DeserializationError, ValidationError, ClientRequestError
from azure.mgmt.batch import BatchManagementClient
from azure.mgmt.batch.models import (BatchAccountCreateParameters,
                                     AutoStorageBaseProperties,
                                     UpdateApplicationParameters)
from azure.mgmt.batch.operations import (ApplicationPackageOperations)

from azure.batch.models import (CertificateAddParameter, PoolStopResizeOptions, PoolResizeParameter,
                                PoolResizeOptions, JobListOptions, JobListFromJobScheduleOptions,
                                TaskAddParameter, TaskConstraints, PoolUpdatePropertiesParameter,
                                StartTask, BatchErrorException)

from azure.storage.blob import BlockBlobService

from azure.cli.core._util import CLIError
from azure.cli.core.commands.client_factory import get_mgmt_service_client
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)

# Mgmt custom commands

def list_accounts(client, resource_group_name=None):
    acct_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(acct_list)


def create_account(client, resource_group_name, account_name, location,  # pylint:disable=too-many-arguments
                   tags=None, storage_account_id=None):
    if storage_account_id:
        properties = AutoStorageBaseProperties(storage_account_id=storage_account_id)
    else:
        properties = None

    parameters = BatchAccountCreateParameters(location=location,
                                              tags=tags,
                                              auto_storage=properties)

    return client.create(resource_group_name=resource_group_name,
                         account_name=account_name,
                         parameters=parameters)

create_account.__doc__ = AutoStorageBaseProperties.__doc__


def update_account(client, resource_group_name, account_name,  # pylint:disable=too-many-arguments
                   tags=None, storage_account_id=None):
    if storage_account_id:
        properties = AutoStorageBaseProperties(storage_account_id=storage_account_id)
    else:
        properties = None

    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         tags=tags,
                         auto_storage=properties)

update_account.__doc__ = AutoStorageBaseProperties.__doc__


def update_application(client, resource_group_name, account_name, application_id, # pylint:disable=too-many-arguments
                       allow_updates=None, display_name=None, default_version=None):
    parameters = UpdateApplicationParameters(allow_updates=allow_updates,
                                             display_name=display_name,
                                             default_version=default_version)
    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         application_id=application_id,
                         parameters=parameters)

update_application.__doc__ = UpdateApplicationParameters.__doc__


def _upload_package_blob(package_file, url):
    """Upload the location file to storage url provided by autostorage"""

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


def create_application_package(client, resource_group_name, account_name, # pylint:disable=too-many-arguments
                               application_id, version, package_file):

    # create application if not exist
    mgmt_client = get_mgmt_service_client(BatchManagementClient)
    try:
        mgmt_client.application.get(resource_group_name, account_name, application_id)
    except:  # pylint:disable=W0702
        mgmt_client.application.create(resource_group_name, account_name, application_id)

    result = client.create(resource_group_name, account_name, application_id, version)

    # upload binary as application package
    logger.info('Uploading %s to storage blob %s...', package_file, result.storage_url)
    _upload_package_blob(package_file, result.storage_url)

    # activate the application package
    client.activate(resource_group_name, account_name, application_id, version, "zip")
    return client.get(resource_group_name, account_name, application_id, version)

create_application_package.__doc__ = ApplicationPackageOperations.create.__doc__


# Data plane custom commands

def create_certificate(client, cert_file, thumbprint, thumbprint_algorithm, password=None):
    if password:
        certificate_format = 'pfx'
    else:
        certificate_format = 'cer'
    with open(cert_file, "rb") as f:
        data_bytes = f.read()
    data = base64.b64encode(data_bytes).decode('utf-8')
    cert = CertificateAddParameter(thumbprint, thumbprint_algorithm, data,
                                   certificate_format=certificate_format,
                                   password=password)
    try:
        client.add(cert)
        return client.get(thumbprint_algorithm, thumbprint)
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

create_application_package.__doc__ = CertificateAddParameter.__doc__


def delete_certificate(client, thumbprint, thumbprint_algorithm, abort=None):
    try:
        if abort:
            client.cancel_deletion(thumbprint_algorithm, thumbprint)
        else:
            client.delete(thumbprint_algorithm, thumbprint)
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


def resize_pool(client, pool_id, target_dedicated=None,  # pylint:disable=too-many-arguments
                resize_timeout=None, node_deallocation_option=None,
                if_match=None, if_none_match=None, if_modified_since=None,
                if_unmodified_since=None, abort=None):
    if abort:
        stop_resize_option = PoolStopResizeOptions(if_match=if_match,
                                                   if_none_match=if_none_match,
                                                   if_modified_since=if_modified_since,
                                                   if_unmodified_since=if_unmodified_since)
        return client.stop_resize(pool_id, pool_stop_resize_options=stop_resize_option)
    else:
        param = PoolResizeParameter(target_dedicated,
                                    resize_timeout=resize_timeout,
                                    node_deallocation_option=node_deallocation_option)
        resize_option = PoolResizeOptions(if_match=if_match,
                                          if_none_match=if_none_match,
                                          if_modified_since=if_modified_since,
                                          if_unmodified_since=if_unmodified_since)

    try:
        return client.resize(pool_id, param, pool_resize_options=resize_option)
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

resize_pool.__doc__ = PoolResizeParameter.__doc__


def update_pool(client, pool_id, json_file=None, command_line=None,  # pylint:disable=too-many-arguments, W0613
                certificate_references=None, application_package_references=None, metadata=None):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            param = None
            try:
                param = client._deserialize('PoolUpdatePropertiesParameter', json_obj)  # pylint:disable=W0212
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

        if command_line:
            param.start_task = StartTask(command_line)

    try:
        client.update_properties(pool_id=pool_id, pool_update_properties_parameter=param)
        return client.get(pool_id)
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

update_pool.__doc__ = PoolUpdatePropertiesParameter.__doc__ + "\n" + StartTask.__doc__


def list_job(client, job_schedule_id=None, filter=None, select=None, expand=None):  # pylint:disable=W0622
    try:
        if job_schedule_id:
            option1 = JobListFromJobScheduleOptions(filter=filter,
                                                    select=select,
                                                    expand=expand)
            return list(client.list_from_job_schedule(job_schedule_id=job_schedule_id,
                                                      job_list_from_job_schedule_options=option1))
        else:
            option2 = JobListOptions(filter=filter,
                                     select=select,
                                     expand=expand)
            return list(client.list(job_list_options=option2))
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


def create_task(client, job_id, json_file=None, task_id=None, command_line=None,  # pylint:disable=too-many-arguments
                resource_files=None, environment_settings=None, affinity_info=None,
                max_wall_clock_time=None, retention_time=None, max_task_retry_count=None,
                run_elevated=None, application_package_references=None):
    task = None
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            try:
                task = client._deserialize('TaskAddParameter', json_obj)  # pylint:disable=W0212
            except DeserializationError:
                try:
                    tasks = client._deserialize('[TaskAddParameter]', json_obj)  # pylint:disable=W0212
                except DeserializationError:
                    raise ValueError("JSON file '{}' is not in reqired format.".format(json_file))
    else:
        task = TaskAddParameter(task_id, command_line,
                                resource_files=resource_files,
                                environment_settings=environment_settings,
                                affinity_info=affinity_info,
                                run_elevated=run_elevated,
                                application_package_references=application_package_references)
        if max_wall_clock_time is not None or retention_time is not None \
            or max_task_retry_count is not None:
            task.constraints = TaskConstraints(max_wall_clock_time=max_wall_clock_time,
                                               retention_time=retention_time,
                                               max_task_retry_count=max_task_retry_count)

    try:
        if task is not None:
            client.add(job_id=job_id, task=task)
            return client.get(job_id=job_id, task_id=task.id)
        else:
            result = client.add_collection(job_id=job_id, value=tasks)
            return result.value
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

create_task.__doc__ = TaskAddParameter.__doc__ + "\n" + TaskConstraints.__doc__
