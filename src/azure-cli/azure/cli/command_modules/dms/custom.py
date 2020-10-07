# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import os
from enum import Enum
from knack.prompting import prompt, prompt_pass
from knack.util import CLIError

from azure.mgmt.datamigration.models import (DataMigrationService,
                                             ServiceSku,
                                             Project,
                                             SqlConnectionInfo,
                                             MigrateSqlServerSqlDbTaskProperties,
                                             MigrateSqlServerSqlDbTaskInput,
                                             MigrateSqlServerSqlDbDatabaseInput,
                                             MigrationValidationOptions)
from azure.cli.core.util import sdk_no_wait, get_file_json, shell_safe_json_parse


# region Service

def check_service_name_availability(client, service_name, location):
    return client.check_name_availability(location=location,
                                          name=service_name,
                                          type='services')


def create_service(client,
                   service_name,
                   resource_group_name,
                   location,
                   subnet,
                   sku_name,
                   tags=None,
                   no_wait=False):
    parameters = DataMigrationService(location=location,
                                      virtual_subnet_id=subnet,
                                      sku=ServiceSku(name=sku_name),
                                      tags=tags)

    return sdk_no_wait(no_wait,
                       client.create_or_update,
                       parameters=parameters,
                       group_name=resource_group_name,
                       service_name=service_name)


def delete_service(client, service_name, resource_group_name, delete_running_tasks=None, no_wait=False):
    return sdk_no_wait(no_wait,
                       client.delete,
                       group_name=resource_group_name,
                       service_name=service_name,
                       delete_running_tasks=delete_running_tasks)


def list_services(client, resource_group_name=None):
    list_func = client.list_by_resource_group(group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list_func


def start_service(client, service_name, resource_group_name, no_wait=False):
    return sdk_no_wait(no_wait,
                       client.start,
                       group_name=resource_group_name,
                       service_name=service_name)


def stop_service(client, service_name, resource_group_name, no_wait=False):
    return sdk_no_wait(no_wait,
                       client.stop,
                       group_name=resource_group_name,
                       service_name=service_name)

# endregion


# region Project

def check_project_name_availability(client, resource_group_name, service_name, project_name):
    return client.check_children_name_availability(group_name=resource_group_name,
                                                   service_name=service_name,
                                                   name=project_name,
                                                   type='projects')


def create_or_update_project(client,
                             project_name,
                             service_name,
                             resource_group_name,
                             location,
                             source_platform,
                             target_platform,
                             tags=None):
    """This implementation eschews the source and target connection details and the database list. This is because this
    generally only helps in a GUI context--to guide the user more easily through creating a task. Since this info is
    necessary at the Task level, there is no need to include it at the Project level where for CLI it is more of a
    useless redundancy."""

    # Set inputs to lowercase
    source_platform = source_platform.lower()
    target_platform = target_platform.lower()

    scenario_handled_in_core = core_handles_scenario(source_platform, target_platform)

    # Validation: Test scenario eligibility
    if not scenario_handled_in_core:
        raise CLIError("The provided source-platform, target-platform combination is not appropriate. \n\
Please refer to the help file 'az dms project create -h' for the supported scenarios.")

    parameters = Project(location=location,
                         source_platform=source_platform,
                         target_platform=target_platform,
                         tags=tags)

    return client.create_or_update(parameters=parameters,
                                   group_name=resource_group_name,
                                   service_name=service_name,
                                   project_name=project_name)

# endregion


# region Task

def check_task_name_availability(client, resource_group_name, service_name, project_name, task_name):
    # because the URL to check for tasks needs to look like this:
    # /subscriptions/{subscription}/resourceGroups/{resourcegroup}/providers/Microsoft.DataMigration/services/{service}/projects/{project}/checkNameAvailability?api-version={version}  # pylint: disable=line-too-long
    # But check_children_name_availability only builds a URL that would check for projects, so we cheat a little by
    # making the service name include the project portion as well.
    return client.check_children_name_availability(group_name=resource_group_name,
                                                   service_name=service_name + '/projects/' + project_name,
                                                   name=task_name,
                                                   type='tasks')


def create_task(client,
                resource_group_name,
                service_name,
                project_name,
                task_name,
                source_connection_json,
                target_connection_json,
                database_options_json,
                enable_schema_validation=False,
                enable_data_integrity_validation=False,
                enable_query_analysis_validation=False):
    if os.path.exists(source_connection_json):
        source_connection_json = get_file_json(source_connection_json)
    else:
        source_connection_json = shell_safe_json_parse(source_connection_json)

    source_connection_info = create_sql_connection_info(source_connection_json, 'Source Database ')

    if os.path.exists(target_connection_json):
        target_connection_json = get_file_json(target_connection_json)
    else:
        target_connection_json = shell_safe_json_parse(target_connection_json)

    target_connection_info = create_sql_connection_info(target_connection_json, 'Target Database ')

    if os.path.exists(database_options_json):
        database_options_json = get_file_json(database_options_json)
    else:
        database_options_json = shell_safe_json_parse(database_options_json)

    database_options = []
    for d in database_options_json:
        database_options.append(
            MigrateSqlServerSqlDbDatabaseInput(name=d.get('name', None),
                                               target_database_name=d.get('target_database_name', None),
                                               make_source_db_read_only=d.get('make_source_db_read_only', None),
                                               table_map=d.get('table_map', None)))

    validation_options = MigrationValidationOptions(enable_schema_validation=enable_schema_validation,
                                                    enable_data_integrity_validation=enable_data_integrity_validation,
                                                    enable_query_analysis_validation=enable_query_analysis_validation)

    task_input = MigrateSqlServerSqlDbTaskInput(source_connection_info=source_connection_info,
                                                target_connection_info=target_connection_info,
                                                selected_databases=database_options,
                                                validation_options=validation_options)

    migration_properties = MigrateSqlServerSqlDbTaskProperties(input=task_input)

    return client.create_or_update(group_name=resource_group_name,
                                   service_name=service_name,
                                   project_name=project_name,
                                   task_name=task_name,
                                   properties=migration_properties)


def list_tasks(client, resource_group_name, service_name, project_name, task_type=None):
    return client.tasks.list(group_name=resource_group_name,
                             service_name=service_name,
                             project_name=project_name,
                             task_type=task_type)

# endregion


# region Helper Methods
def create_sql_connection_info(connection_info_json, prompt_prefix):
    return SqlConnectionInfo(
        user_name=connection_info_json.get('userName', None) or prompt(prompt_prefix + 'Username: '),
        password=connection_info_json.get('password', None) or prompt_pass(msg=prompt_prefix + 'Password: '),
        data_source=connection_info_json.get('dataSource', None),
        authentication=connection_info_json.get('authentication', None),
        encrypt_connection=connection_info_json.get('encryptConnection', None),
        trust_server_certificate=connection_info_json.get('trustServerCertificate', None),
        additional_settings=connection_info_json.get('additionalSettings', None))


def core_handles_scenario(
        source_platform,
        target_platform,
        task_type=""):
    # Add scenarios here after migrating them to the core from the extension.
    CoreScenarioTypes = [
            ScenarioType.sql_sqldb_offline,
            ScenarioType.mysql_azuremysql_online,
            ScenarioType.postgres_azurepostgres_online]
    return get_scenario_type(source_platform, target_platform, task_type) in CoreScenarioTypes


def get_scenario_type(source_platform, target_platform, task_type=""):
    if source_platform == "sql" and target_platform == "sqldb":
        scenario_type = ScenarioType.sql_sqldb_offline if not task_type or "offline" in task_type else ScenarioType.unknown
    elif source_platform == "mysql" and target_platform == "azuredbformysql":
        scenario_type = ScenarioType.mysql_azuremysql_online if not task_type or "online" in task_type else ScenarioType.unknown
    elif source_platform == "postgresql" and target_platform == "azuredbforpostgresql":
        scenario_type = ScenarioType.postgres_azurepostgres_online if not task_type or "online" in task_type else \
            ScenarioType.unkown
    else:
        scenario_type = ScenarioType.unknown

    return scenario_type


class ScenarioType(Enum):

        unknown = 0
        # SQL to SQLDB
        sql_sqldb_offline = 1
        # MySQL to Azure for MySQL
        mysql_azuremysql_online = 21
        # PostgresSQL to Azure for PostgreSQL
        postgres_azurepostgres_online = 31

# endregion
