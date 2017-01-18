# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit # pylint: disable=import-error
import json
import io
import base64

from azure.mgmt.batch import BatchManagementClient
from azure.mgmt.batch.models import (BatchAccountCreateParameters,
                                     AutoStorageBaseProperties,
                                     UpdateApplicationParameters)
from azure.mgmt.batch.operations import (ApplicationPackageOperations)

from azure.batch.models import (PoolAddParameter, JobUpdateParameter,
                                CertificateAddParameter, PoolUpdatePropertiesParameter,
                                PoolPatchParameter, PoolPatchOptions,
                                PoolStopResizeOptions, PoolResizeParameter,
                                PoolResizeOptions, PoolInformation,
                                JobAddParameter, JobConstraints,
                                JobListOptions, JobListFromJobScheduleOptions,
                                JobUpdateOptions, JobPatchParameter,
                                JobPatchOptions, Schedule,
                                JobSpecification, JobScheduleAddParameter,
                                JobScheduleUpdateParameter, JobScheduleUpdateOptions,
                                JobSchedulePatchParameter, JobSchedulePatchOptions,
                                TaskAddParameter, TaskConstraints,
                                CloudServiceConfiguration, VirtualMachineConfiguration,
                                ImageReference, StartTask, ApplicationPackageReference,
                                MetadataItem, CertificateReference)

from azure.storage.blob import BlockBlobService

from azure.cli.core.commands.client_factory import get_mgmt_service_client
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)

def list_accounts(client, resource_group_name=None):
    acct_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(acct_list)

def create_account(client, resource_group_name, account_name, location, #pylint:disable=too-many-arguments
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

def update_account(client, resource_group_name, account_name,  #pylint:disable=too-many-arguments
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

def update_application(client, resource_group_name, account_name, application_id, #pylint:disable=too-many-arguments
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

def create_application_package(client, resource_group_name, account_name, #pylint:disable=too-many-arguments
                               application_id, version, package_file):

    # create application if not exist
    mgmt_client = get_mgmt_service_client(BatchManagementClient)
    try:
        mgmt_client.application.get(resource_group_name, account_name, application_id)
    except: 
        mgmt_client.application.create(resource_group_name, account_name, application_id)

    result = client.create(resource_group_name, account_name, application_id, version)

    # upload binary as application package
    logger.info('Uploading %s to storage blob %s...', package_file, result.storage_url)
    _upload_package_blob(package_file, result.storage_url)

    # activate the application package
    client.activate(resource_group_name, account_name, application_id, version, "zip")
    return client.get(resource_group_name, account_name, application_id, version)


create_application_package.__doc__ = ApplicationPackageOperations.create.__doc__

def create_certificate(client, cert_file, thumbprint, thumbprint_algorithm, password=None, **kwarg): #pylint:disable=W0613
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
    client.add(cert)
    return client.get(thumbprint_algorithm, thumbprint)

create_application_package.__doc__ = CertificateAddParameter.__doc__

def delete_certificate(client, thumbprint, thumbprint_algorithm, abort=None, **kwarg): #pylint:disable=W0613
    if abort:
        client.cancel_deletion(thumbprint_algorithm, thumbprint)
    else:
        client.delete(thumbprint_algorithm, thumbprint)

def create_pool(client, json_file=None, pool_id=None, vm_size=None, target_dedicated=None, #pylint:disable=too-many-arguments, W0613
                auto_scale_formula=None, os_family=None, image_publisher=None,
                image_offer=None, image_sku=None, node_agent_sku_id=None, resize_timeout=None,
                start_task_cmd=None, certificate_references=None,
                application_package_references=None, metadata=None, **kwarg):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            pool = client._deserialize('PoolAddParameter', json_obj) #pylint:disable=W0212
            if pool is None:
                raise ValueError("JSON file '{}' is not in correct format.".format(json_file))
    else:
        pool = PoolAddParameter(pool_id, vm_size=vm_size)
        if target_dedicated is not None:
            pool.target_dedicated = target_dedicated
            pool.enable_auto_scale = False
        else:
            pool.auto_scale_formula = auto_scale_formula
            pool.enable_auto_scale = True

        if os_family:
            pool.cloud_service_configuration = CloudServiceConfiguration(os_family)
        else:
            pool.virtual_machine_configuration = VirtualMachineConfiguration(
                ImageReference(image_publisher, image_offer, image_sku),
                node_agent_sku_id)

        if start_task_cmd:
            pool.start_task = StartTask(start_task_cmd)
        if resize_timeout:
            pool.resize_timeout = resize_timeout

        if metadata is not None:
            pool.metadata = [MetadataItem(x, metadata[x]) for x in metadata]
        if certificate_references is not None:
            pool.certificate_references = \
                [CertificateReference(x, 'sha1') for x in certificate_references]
        if application_package_references is not None:
            pool.application_package_references = \
                [ApplicationPackageReference(x) for x in application_package_references]

    client.add(pool=pool)
    return client.get(pool.id)

create_pool.__doc__ = PoolAddParameter.__doc__

def update_pool(client, pool_id, json_file=None, start_task_cmd=None, #pylint:disable=too-many-arguments, W0613
                certificate_references=None, application_package_references=None,
                metadata=None, **kwarg):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            param = client._deserialize('PoolUpdatePropertiesParameter', json_obj) #pylint:disable=W0212
            if param is None:
                raise ValueError("JSON file '{}' is not in correct format.".format(json_file))
    else:
        param = PoolUpdatePropertiesParameter(pool_id, \
                    [CertificateReference(x, 'sha1') for x in certificate_references], \
                    [ApplicationPackageReference(x) for x in application_package_references], \
                    [MetadataItem(x, metadata[x]) for x in metadata])

        if start_task_cmd:
            param.start_task = StartTask(start_task_cmd)

    client.update_properties(pool_id=pool_id, pool_update_properties_parameter=param)
    return client.get(pool_id)

update_pool.__doc__ = PoolUpdatePropertiesParameter.__doc__

def patch_pool(client, pool_id, json_file=None, start_task_cmd=None, #pylint:disable=too-many-arguments, W0613
               if_match=None, if_none_match=None, if_modified_since=None, if_unmodified_since=None,
               certificate_references=None, application_package_references=None,
               metadata=None, **kwarg):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            param = client._deserialize('PoolPatchParameter', json_obj) #pylint:disable=W0212
            if param:
                raise ValueError("JSON file '{}' is not in correct format.".format(json_file))
    else:
        param = PoolPatchParameter(pool_id)

        if start_task_cmd:
            param.start_task = StartTask(start_task_cmd)

        if metadata is not None:
            param.metadata = [MetadataItem(x, metadata[x]) for x in metadata]
        if certificate_references is not None:
            param.certificate_references = [CertificateReference(x, 'sha1') \
                for x in certificate_references]
        if application_package_references is not None:
            param.application_package_references = \
                [ApplicationPackageReference(x) for x in application_package_references]

    option = PoolPatchOptions(if_match=if_match,
                              if_none_match=if_none_match,
                              if_modified_since=if_modified_since,
                              if_unmodified_since=if_unmodified_since)
    client.patch(pool_id=pool_id, pool_patch_parameter=param, pool_patch_options=option)
    return client.get(pool_id)

patch_pool.__doc__ = PoolPatchParameter.__doc__

def resize_pool(client, pool_id, target_dedicated=None, #pylint:disable=too-many-arguments, W0613
                resize_timeout=None, node_deallocation_option=None,
                if_match=None, if_none_match=None, if_modified_since=None,
                if_unmodified_since=None, abort=None, **kwarg):
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

        return client.resize(pool_id, param, pool_resize_options=resize_option)

resize_pool.__doc__ = PoolResizeParameter.__doc__

def create_job(client, json_file=None, job_id=None, pool_id=None, priority=None, #pylint:disable=too-many-arguments, W0613
               max_wall_clock_time=None, max_task_retry_count=None,
               metadata=None, **kwarg):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            job = client._deserialize('JobAddParameter', json_obj) #pylint:disable=W0212
            if job is None:
                raise ValueError("JSON file '{}' is not in correct format.".format(json_file))
    else:
        pool = PoolInformation(pool_id=pool_id)
        job = JobAddParameter(job_id, pool, priority=priority)
        if max_wall_clock_time is not None or max_task_retry_count is not None:
            constraints = JobConstraints(max_wall_clock_time=max_wall_clock_time,
                                         max_task_retry_count=max_task_retry_count)
            job.constraints = constraints

        if metadata is not None:
            job.metadata = [MetadataItem(x, metadata[x]) for x in metadata]

    client.add(job)
    return client.get(job.id)

create_job.__doc__ = JobAddParameter.__doc__ + "\n" + JobConstraints.__doc__

def list_job(client, job_schedule_id=None, filter=None, select=None, expand=None, **kwarg): #pylint:disable= W0613, W0622
    if job_schedule_id:
        option1 = JobListFromJobScheduleOptions(filter=filter,
                                                select=select,
                                                expand=expand)
        return client.list_from_job_schedule(job_schedule_id=job_schedule_id,
                                             job_list_from_job_schedule_options=option1)
    else:
        option2 = JobListOptions(filter=filter,
                                 select=select,
                                 expand=expand)
        return client.list(job_list_options=option2)

def update_job(client, job_id, json_file=None, pool_id=None, priority=None, #pylint:disable=too-many-arguments, W0613
               max_wall_clock_time=None, max_task_retry_count=None,
               if_match=None, if_none_match=None, if_modified_since=None, if_unmodified_since=None,
               metadata=None, **kwarg):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            param = client._deserialize('JobUpdateParameter', json_obj) #pylint:disable=W0212
            if param is None:
                raise ValueError("JSON file '{}' is not in correct format.".format(json_file))
    else:
        pool = PoolInformation(pool_id=pool_id)
        param = JobUpdateParameter(pool, priority=priority)
        if max_wall_clock_time is not None or max_task_retry_count is not None:
            constraints = JobConstraints(max_wall_clock_time=max_wall_clock_time,
                                         max_task_retry_count=max_task_retry_count)
            param.constraints = constraints

        if metadata is not None:
            param.metadata = [MetadataItem(x, metadata[x]) for x in metadata]

    option = JobUpdateOptions(if_match=if_match,
                              if_none_match=if_none_match,
                              if_modified_since=if_modified_since,
                              if_unmodified_since=if_unmodified_since)
    client.update(job_id, param, job_update_options=option)
    return client.get(job_id)

update_job.__doc__ = JobUpdateParameter.__doc__ + "\n" + JobConstraints.__doc__

def patch_job(client, job_id, json_file=None, pool_id=None, priority=None, #pylint:disable=too-many-arguments, W0613
              max_wall_clock_time=None, max_task_retry_count=None,
              if_match=None, if_none_match=None, if_modified_since=None, if_unmodified_since=None,
              metadata=None, **kwarg):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            param = client._deserialize('JobPatchParameter', json_obj) #pylint:disable=W0212
            if param is None:
                raise ValueError("JSON file '{}' is not in correct format.".format(json_file))
    else:
        pool = PoolInformation(pool_id=pool_id)
        param = JobPatchParameter(pool_info=pool, priority=priority)
        if max_wall_clock_time is not None or max_task_retry_count is not None:
            constraints = JobConstraints(max_wall_clock_time=max_wall_clock_time,
                                         max_task_retry_count=max_task_retry_count)
            param.constraints = constraints

        if metadata is not None:
            param.metadata = [MetadataItem(x, metadata[x]) for x in metadata]

    option = JobPatchOptions(if_match=if_match,
                             if_none_match=if_none_match,
                             if_modified_since=if_modified_since,
                             if_unmodified_since=if_unmodified_since)
    client.patch(job_id, param, job_patch_options=option)
    return client.get(job_id)

patch_job.__doc__ = JobPatchParameter.__doc__ + "\n" + JobConstraints.__doc__

def create_job_schedule(client, json_file=None, job_schedule_id=None, pool_id=None, priority=None, #pylint:disable=too-many-arguments, W0613
                        max_wall_clock_time=None, max_task_retry_count=None, do_not_run_until=None,
                        do_not_run_after=None, start_window=None, recurrence_interval=None,
                        metadata=None, **kwarg):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            job_schedule = client._deserialize('JobScheduleAddParameter', json_obj) #pylint:disable=W0212
            if job_schedule is None:
                raise ValueError("JSON file '{}' is not in correct format.".format(json_file))
    else:
        schedule = Schedule(do_not_run_until=do_not_run_until,
                            do_not_run_after=do_not_run_after,
                            start_window=start_window,
                            recurrence_interval=recurrence_interval)
        pool = PoolInformation(pool_id=pool_id)
        job_spec = JobSpecification(pool, priority=priority)
        if max_wall_clock_time is not None or max_task_retry_count is not None:
            constraints = JobConstraints(max_wall_clock_time=max_wall_clock_time,
                                         max_task_retry_count=max_task_retry_count)
            job_spec.constraints = constraints

        job_schedule = JobScheduleAddParameter(job_schedule_id, schedule, job_spec)
        if metadata is not None:
            job_schedule.metadata = [MetadataItem(x, metadata[x]) for x in metadata]

    client.add(job_schedule)
    return client.get(job_schedule.id)

create_job_schedule.__doc__ = Schedule.__doc__ + "\n" + JobConstraints.__doc__

def update_job_schedule(client, job_schedule_id, json_file=None, pool_id=None, priority=None, #pylint:disable=too-many-arguments, W0613
                        max_wall_clock_time=None, max_task_retry_count=None, do_not_run_until=None,
                        do_not_run_after=None, start_window=None, recurrence_interval=None,
                        if_match=None, if_none_match=None, if_modified_since=None,
                        if_unmodified_since=None, metadata=None, **kwarg):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            param = client._deserialize('JobScheduleUpdateParameter', json_obj) #pylint:disable=W0212
            if param is None:
                raise ValueError("JSON file '{}' is not in correct format.".format(json_file))
    else:
        if do_not_run_until is not None or do_not_run_after is not None or \
            start_window is not None or recurrence_interval is not None:
            schedule = Schedule(do_not_run_until=do_not_run_until,
                                do_not_run_after=do_not_run_after,
                                start_window=start_window,
                                recurrence_interval=recurrence_interval)

        if pool_id is not None:
            pool = PoolInformation(pool_id=pool_id)
            job_spec = JobSpecification(pool, priority=priority)
            if max_wall_clock_time is not None or max_task_retry_count is not None:
                job_spec.constraints = JobConstraints(max_wall_clock_time=max_wall_clock_time,
                                                      max_task_retry_count=max_task_retry_count)

        param = JobScheduleUpdateParameter(schedule, job_spec)

        if metadata is not None:
            param.metadata = [MetadataItem(x, metadata[x]) for x in metadata]

    option = JobScheduleUpdateOptions(if_match=if_match,
                                      if_none_match=if_none_match,
                                      if_modified_since=if_modified_since,
                                      if_unmodified_since=if_unmodified_since)
    client.update(job_schedule_id, param, job_schedule_update_options=option)
    return client.get(job_schedule_id)

update_job_schedule.__doc__ = Schedule.__doc__ + "\n" + JobConstraints.__doc__

def patch_job_schedule(client, job_schedule_id, json_file=None, pool_id=None, priority=None, #pylint:disable=too-many-arguments, W0613
                       max_wall_clock_time=None, max_task_retry_count=None, do_not_run_until=None,
                       do_not_run_after=None, start_window=None, recurrence_interval=None,
                       if_match=None, if_none_match=None, if_modified_since=None,
                       if_unmodified_since=None, metadata=None, **kwarg):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            param = client._deserialize('JobSchedulePatchParameter', json_obj) #pylint:disable=W0212
            if param is None:
                raise ValueError("JSON file '{}' is not in correct format.".format(json_file))
    else:
        param = JobSchedulePatchParameter()
        if do_not_run_until is not None or do_not_run_after is not None or \
            start_window is not None or recurrence_interval is not None:
            param.schedule = Schedule(do_not_run_until=do_not_run_until,
                                      do_not_run_after=do_not_run_after,
                                      start_window=start_window,
                                      recurrence_interval=recurrence_interval)

        if pool_id is not None:
            pool = PoolInformation(pool_id=pool_id)
            job_spec = JobSpecification(pool, priority=priority)
            if max_wall_clock_time is not None or max_task_retry_count is not None:
                job_spec.constraints = JobConstraints(max_wall_clock_time=max_wall_clock_time,
                                                      max_task_retry_count=max_task_retry_count)
            param.job_specification = job_spec

        if metadata is not None:
            param.metadata = [MetadataItem(x, metadata[x]) for x in metadata]

    option = JobSchedulePatchOptions(if_match=if_match,
                                     if_none_match=if_none_match,
                                     if_modified_since=if_modified_since,
                                     if_unmodified_since=if_unmodified_since)
    client.patch(job_schedule_id, param, job_schedule_patch_options=option)
    return client.get(job_schedule_id)

patch_job_schedule.__doc__ = Schedule.__doc__ + "\n" + JobConstraints.__doc__

def create_task(client, job_id, json_file=None, task_id=None, command_line=None,  #pylint:disable=too-many-arguments, W0613
                resource_files=None, environment_settings=None, affinity_info=None,
                max_wall_clock_time=None, retention_time=None, max_task_retry_count=None,
                run_elevated=None, application_package_references=None, **kwarg):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            task = client._deserialize('TaskAddParameter', json_obj) #pylint:disable=W0212
            if task is None:
                tasks = client._deserialize('TaskAddCollectionParameter', json_obj) #pylint:disable=W0212
            if task is None and tasks is None:
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

    if task is not None:
        return client.add(job_id=job_id,
                          task=task)
    else:
        return client.add_collection(job_id=job_id,
                                     value=tasks)

create_task.__doc__ = TaskAddParameter.__doc__ + "\n" + TaskConstraints.__doc__
