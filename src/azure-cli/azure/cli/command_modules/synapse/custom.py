# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

from azure.synapse.models import ExtendedLivyBatchRequest, LivyStatementRequestBody, ExtendedLivySessionRequest

from azure.mgmt.synapse.models import Workspace, ManagedIdentity, DataLakeStorageAccountDetails, \
    BigDataPoolResourceInfo, AutoScaleProperties, AutoPauseProperties, LibraryRequirements, NodeSize, NodeSizeFamily

logger = get_logger(__name__)


# pylint: disable=too-many-locals, too-many-branches, too-many-statements, unused-argument
def list_spark_batch_jobs(cmd, client, workspace_name, spark_pool_name, from_index=None, size=None, detailed=True):
    return client.list(workspace_name, spark_pool_name, from_index, size, detailed)


def create_spark_batch_job(cmd, client, workspace_name, spark_pool_name, job_name, file, class_name,
                           args, driver_memory, driver_cores, executor_memory, executor_cores,
                           num_executors, jars=None, files=None, archives=None, conf=None, artifact_id=None,
                           tags=None, detailed=True):
    livy_batch_request = ExtendedLivyBatchRequest(
        tags=tags, artifact_id=artifact_id,
        name=job_name, file=file, class_name=class_name, args=args, jars=jars, files=files, archives=archives,
        conf=conf, driver_memory=driver_memory, driver_cores=driver_cores, executor_memory=executor_memory,
        executor_cores=executor_cores, num_executors=num_executors)

    return client.create(workspace_name, spark_pool_name, livy_batch_request, detailed)


def get_spark_batch_job(cmd, client, workspace_name, spark_pool_name, batch_id, detailed=True):
    return client.get(workspace_name, spark_pool_name, batch_id, detailed)


def cancel_spark_batch_job(cmd, client, workspace_name, spark_pool_name, batch_id):
    return client.delete(workspace_name, spark_pool_name, batch_id)


# Spark Session
def list_spark_session_jobs(cmd, client, workspace_name, spark_pool_name, from_index=None, size=None, detailed=True):
    return client.list(workspace_name, spark_pool_name, from_index, size, detailed)


def create_spark_session_job(cmd, client, workspace_name, spark_pool_name, driver_memory, driver_cores,
                             executor_memory, executor_cores, num_executors, job_name=None, file=None, class_name=None,
                             args=None, jars=None, files=None, archives=None, conf=None, artifact_id=None,
                             tags=None, detailed=True):
    livy_session_request = ExtendedLivySessionRequest(
        tags=tags, artifact_id=artifact_id,
        name=job_name, file=file, class_name=class_name, args=args, jars=jars, files=files, archives=archives,
        conf=conf, driver_memory=driver_memory, driver_cores=driver_cores, executor_memory=executor_memory,
        executor_cores=executor_cores, num_executors=num_executors)
    return client.create(workspace_name, spark_pool_name, livy_session_request, detailed)


def get_spark_session_job(cmd, client, workspace_name, spark_pool_name, session_id, detailed=True):
    return client.get(workspace_name, spark_pool_name, session_id, detailed)


def cancel_spark_session_job(cmd, client, workspace_name, spark_pool_name, session_id):
    return client.delete(workspace_name, spark_pool_name, session_id)


def reset_timeout(cmd, client, workspace_name, spark_pool_name, session_id):
    return client.reset_timeout(workspace_name, spark_pool_name, session_id)


def list_spark_session_statements(cmd, client, workspace_name, spark_pool_name, session_id):
    return client.list_statements(workspace_name, spark_pool_name, session_id)


def create_spark_session_statement(cmd, client, workspace_name, spark_pool_name, session_id, code, kind):
    livy_statement_request = LivyStatementRequestBody(code=code, kind=kind)
    return client.create_statement(workspace_name, spark_pool_name, session_id, livy_statement_request)


def get_spark_session_statement(cmd, client, workspace_name, spark_pool_name, session_id, statement_id):
    return client.get_statement(workspace_name, spark_pool_name, session_id, statement_id)


def cancel_spark_session_statement(cmd, client, workspace_name, spark_pool_name, session_id, statement_id):
    return client.delete_statement(workspace_name, spark_pool_name, session_id, statement_id)


def get_workspace(cmd, client, resource_group_name, workspace_name):
    return client.get(resource_group_name, workspace_name)


def list_workspaces(cmd, client, resource_group_name=None):  # pylint: disable=unused-argument
    return client.list_by_resource_group(
        resource_group_name=resource_group_name) if resource_group_name else client.list()


def create_workspace(cmd, client, resource_group_name, workspace_name, account_url, file_system, sql_admin_login_user,
                     sql_admin_login_password, location, tags=None, identity_type="SystemAssigned"):
    identity = ManagedIdentity(type=identity_type)
    default_data_lake_storage = DataLakeStorageAccountDetails(account_url=account_url, filesystem=file_system)
    workspace_info = Workspace(
        identity=identity,
        default_data_lake_storage=default_data_lake_storage,
        sql_administrator_login=sql_admin_login_user,
        sql_administrator_login_password=sql_admin_login_password,
        location=location
    )
    return client.create_or_update(resource_group_name, workspace_name, workspace_info)


def delete_workspace(cmd, client, resource_group_name, workspace_name):
    return client.delete(resource_group_name, workspace_name)


def create_spark_pool(cmd, client, resource_group_name, workspace_name, spark_pool_name, location,
                      spark_version="2.4", node_size=NodeSize.medium.value, node_count=3,
                      node_size_family=NodeSizeFamily.memory_optimized.value, auto_scale_enabled=True,
                      min_node_count=3,
                      max_node_count=40, auto_pause_enabled=True, delay_in_minutes=15, spark_events_folder="/events",
                      library_requirements_filename=None, library_requirements_content=None,
                      default_spark_log_folder="/logs", force=False):
    big_data_pool_info = BigDataPoolResourceInfo(location=location, spark_version=spark_version, node_size=node_size,
                                                 node_count=node_count, node_size_family=node_size_family,
                                                 spark_events_folder=spark_events_folder,
                                                 default_spark_log_folder=default_spark_log_folder)
    if auto_scale_enabled:
        big_data_pool_info.auto_scale = AutoScaleProperties(enabled=auto_scale_enabled, min_node_count=min_node_count,
                                                            max_node_count=max_node_count)
    if auto_pause_enabled:
        big_data_pool_info.auto_pause = AutoPauseProperties(enabled=auto_pause_enabled,
                                                            delay_in_minutes=delay_in_minutes)

    if library_requirements_filename or library_requirements_content:
        big_data_pool_info.library_requirements = LibraryRequirements(filename=library_requirements_filename,
                                                                      content=library_requirements_content)
    return client.create_or_update(resource_group_name, workspace_name, spark_pool_name, big_data_pool_info, force)
