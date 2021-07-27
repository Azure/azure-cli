# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import os
from enum import Enum
from knack.prompting import prompt, prompt_pass
from knack.util import CLIError

from azure.mgmt.datamigration.models import (DataMigrationService,
                                             NameAvailabilityRequest,
                                             MigratePostgreSqlAzureDbForPostgreSqlSyncTaskProperties,
                                             MigrateSqlServerSqlDbTaskProperties,
                                             MigrateSyncCompleteCommandInput,
                                             MigrateSyncCompleteCommandProperties,
                                             MySqlConnectionInfo,
                                             PostgreSqlConnectionInfo,
                                             Project,
                                             ProjectTask,
                                             ServiceSku,
                                             SqlConnectionInfo)
from azure.cli.core.util import sdk_no_wait, get_file_json, shell_safe_json_parse
from azure.cli.command_modules.dms._client_factory import dms_cf_projects
from azure.cli.command_modules.dms.scenario_inputs import (get_migrate_sql_to_sqldb_offline_input,
                                                           get_migrate_postgresql_to_azuredbforpostgresql_sync_input)


# region Service

def check_service_name_availability(client, service_name, location):
    parameters = NameAvailabilityRequest(name=service_name,
                                         type='services')
    return client.check_name_availability(location=location,
                                          parameters=parameters)


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
                       client.begin_create_or_update,
                       parameters=parameters,
                       group_name=resource_group_name,
                       service_name=service_name)


def delete_service(client, service_name, resource_group_name, delete_running_tasks=None, no_wait=False):
    return sdk_no_wait(no_wait,
                       client.begin_delete,
                       group_name=resource_group_name,
                       service_name=service_name,
                       delete_running_tasks=delete_running_tasks)


def list_services(client, resource_group_name=None):
    list_func = client.list_by_resource_group(group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list_func


def start_service(client, service_name, resource_group_name, no_wait=False):
    return sdk_no_wait(no_wait,
                       client.begin_start,
                       group_name=resource_group_name,
                       service_name=service_name)


def stop_service(client, service_name, resource_group_name, no_wait=False):
    return sdk_no_wait(no_wait,
                       client.begin_stop,
                       group_name=resource_group_name,
                       service_name=service_name)

# endregion


# region Project

def check_project_name_availability(client, resource_group_name, service_name, project_name):
    parameters = NameAvailabilityRequest(name=project_name,
                                         type='projects')
    return client.check_children_name_availability(group_name=resource_group_name,
                                                   service_name=service_name,
                                                   parameters=parameters)


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
    parameters = NameAvailabilityRequest(name=task_name,
                                         type='tasks')
    return client.check_children_name_availability(group_name=resource_group_name,
                                                   service_name=service_name + '/projects/' + project_name,
                                                   parameters=parameters)


def create_task(cmd,
                client,
                resource_group_name,
                service_name,
                project_name,
                task_name,
                source_connection_json,
                target_connection_json,
                database_options_json,
                task_type="",
                enable_schema_validation=False,
                enable_data_integrity_validation=False,
                enable_query_analysis_validation=False):

    # Get source and target platform abd set inputs to lowercase
    source_platform, target_platform = get_project_platforms(cmd,
                                                             project_name=project_name,
                                                             service_name=service_name,
                                                             resource_group_name=resource_group_name)
    task_type = task_type.lower()
    scenario_handled_in_core = core_handles_scenario(source_platform,
                                                     target_platform,
                                                     task_type)

    # Validation: Test scenario eligibility
    if not scenario_handled_in_core:
        raise CLIError("The combination of the provided task-type and the project's \
source-platform and target-platform is not appropriate. \n\
Please refer to the help file 'az dms project task create -h' \
for the supported scenarios.")

    source_connection_info, target_connection_info, database_options_json = \
        transform_json_inputs(source_connection_json,
                              source_platform,
                              target_connection_json,
                              target_platform,
                              database_options_json)

    task_properties = get_task_migration_properties(database_options_json,
                                                    source_platform,
                                                    target_platform,
                                                    task_type,
                                                    source_connection_info,
                                                    target_connection_info,
                                                    enable_schema_validation,
                                                    enable_data_integrity_validation,
                                                    enable_query_analysis_validation)

    parameters = ProjectTask(properties=task_properties)
    return client.create_or_update(group_name=resource_group_name,
                                   service_name=service_name,
                                   project_name=project_name,
                                   task_name=task_name,
                                   parameters=parameters)


def list_tasks(client, resource_group_name, service_name, project_name, task_type=None):
    return client.tasks.list(group_name=resource_group_name,
                             service_name=service_name,
                             project_name=project_name,
                             task_type=task_type)


def cutover_sync_task(cmd,
                      client,
                      resource_group_name,
                      service_name,
                      project_name,
                      task_name,
                      object_name):
    # If object name is empty, treat this as cutting over the entire online migration.
    # Otherwise, for scenarios that support it, just cut over the migration on the specified object.
    # 'input' is a built in function. Even though we can technically use it, it's not recommended.
    # https://stackoverflow.com/questions/20670732/is-input-a-keyword-in-python

    source_platform, target_platform = get_project_platforms(cmd,
                                                             project_name=project_name,
                                                             service_name=service_name,
                                                             resource_group_name=resource_group_name)
    st = get_scenario_type(source_platform, target_platform, "onlinemigration")

    if st in [ScenarioType.mysql_azuremysql_online,
              ScenarioType.postgres_azurepostgres_online]:
        command_input = MigrateSyncCompleteCommandInput(database_name=object_name)
        command_properties_model = MigrateSyncCompleteCommandProperties
    else:
        raise CLIError("The supplied project's source and target do not support cutting over the migration.")

    run_command(client,
                command_input,
                command_properties_model,
                resource_group_name,
                service_name,
                project_name,
                task_name)
# endregion


# region Helper Methods
def run_command(client,
                command_input,
                command_properties_model,
                resource_group_name,
                service_name,
                project_name,
                task_name):
    command_properties_params = {'input': command_input}
    command_properties = command_properties_model(**command_properties_params)

    client.command(group_name=resource_group_name,
                   service_name=service_name,
                   project_name=project_name,
                   task_name=task_name,
                   parameters=command_properties)


def get_project_platforms(cmd, project_name, service_name, resource_group_name):
    client = dms_cf_projects(cmd.cli_ctx)
    proj = client.get(group_name=resource_group_name, service_name=service_name, project_name=project_name)
    return (proj.source_platform.lower(), proj.target_platform.lower())


def core_handles_scenario(
        source_platform,
        target_platform,
        task_type=""):
    # Add scenarios here after migrating them to the core from the extension.
    CoreScenarioTypes = [ScenarioType.sql_sqldb_offline,
                         ScenarioType.postgres_azurepostgres_online]
    return get_scenario_type(source_platform, target_platform, task_type) in CoreScenarioTypes


def transform_json_inputs(
        source_connection_json,
        source_platform,
        target_connection_json,
        target_platform,
        database_options_json):
    # Source connection info
    source_connection_json = get_file_or_parse_json(source_connection_json, "source-connection-json")
    source_connection_info = create_connection(source_connection_json, "Source Database ", source_platform)

    # Target connection info
    target_connection_json = get_file_or_parse_json(target_connection_json, "target-connection-json")
    target_connection_info = create_connection(target_connection_json, "Target Database ", target_platform)

    # Database options
    database_options_json = get_file_or_parse_json(database_options_json, "database-options-json")

    return (source_connection_info, target_connection_info, database_options_json)


def get_file_or_parse_json(value, value_type):
    if os.path.exists(value):
        return get_file_json(value)

    # Test if provided value is a valid json
    try:
        json_parse = shell_safe_json_parse(value)
    except:
        raise CLIError("The supplied input for '" + value_type + "' is not a valid file path or a valid json object.")
    else:
        return json_parse


def create_connection(connection_info_json, prompt_prefix, typeOfInfo):
    user_name = connection_info_json.get('userName', None) or prompt(prompt_prefix + 'Username: ')
    password = connection_info_json.get('password', None) or prompt_pass(msg=prompt_prefix + 'Password: ')

    if "mysql" in typeOfInfo:
        server_name = connection_info_json.get('serverName', None)
        port = connection_info_json.get('port', 3306)
        return MySqlConnectionInfo(user_name=user_name,
                                   password=password,
                                   server_name=server_name,
                                   port=port)

    if "postgres" in typeOfInfo:
        server_name = connection_info_json.get('serverName', None)
        database_name = connection_info_json.get('databaseName', "postgres")
        port = connection_info_json.get('port', 5432)
        trust_server_certificate = connection_info_json.get('trustServerCertificate', False)
        encrypt_connection = connection_info_json.get('encryptConnection', True)
        return PostgreSqlConnectionInfo(user_name=user_name,
                                        password=password,
                                        server_name=server_name,
                                        database_name=database_name,
                                        port=port,
                                        encrypt_connection=encrypt_connection,
                                        trust_server_certificate=trust_server_certificate)

    if "sql" in typeOfInfo:
        data_source = connection_info_json.get('dataSource', None)
        authentication = connection_info_json.get('authentication', None)
        encrypt_connection = connection_info_json.get('encryptConnection', None)
        trust_server_certificate = connection_info_json.get('trustServerCertificate', None)
        additional_settings = connection_info_json.get('additionalSettings', None)
        return SqlConnectionInfo(user_name=user_name,
                                 password=password,
                                 data_source=data_source,
                                 authentication=authentication,
                                 encrypt_connection=encrypt_connection,
                                 trust_server_certificate=trust_server_certificate,
                                 additional_settings=additional_settings)

    # If no match, Pass the connection info through
    return connection_info_json


def get_task_migration_properties(
        database_options_json,
        source_platform,
        target_platform,
        task_type,
        source_connection_info,
        target_connection_info,
        enable_schema_validation,
        enable_data_integrity_validation,
        enable_query_analysis_validation):
    st = get_scenario_type(source_platform, target_platform, task_type)
    if st == ScenarioType.sql_sqldb_offline:
        TaskProperties = MigrateSqlServerSqlDbTaskProperties
        GetInput = get_migrate_sql_to_sqldb_offline_input
    elif st == ScenarioType.postgres_azurepostgres_online:
        TaskProperties = MigratePostgreSqlAzureDbForPostgreSqlSyncTaskProperties
        GetInput = get_migrate_postgresql_to_azuredbforpostgresql_sync_input
    else:
        raise CLIError("The supplied source, target, and task type is not supported for migration.")

    return get_task_properties(st,
                               GetInput,
                               TaskProperties,
                               database_options_json,
                               source_connection_info,
                               target_connection_info,
                               enable_schema_validation,
                               enable_data_integrity_validation,
                               enable_query_analysis_validation)


def get_task_properties(scenario_type,
                        input_func,
                        task_properties_type,
                        options_json,
                        source_connection_info,
                        target_connection_info,
                        enable_schema_validation,
                        enable_data_integrity_validation,
                        enable_query_analysis_validation):
    if source_connection_info is None and target_connection_info is None:
        task_input = input_func(options_json)
    elif scenario_type == ScenarioType.sql_sqldb_offline:
        task_input = input_func(
            options_json,
            source_connection_info,
            target_connection_info,
            enable_schema_validation,
            enable_data_integrity_validation,
            enable_query_analysis_validation)
    else:
        task_input = input_func(
            options_json,
            source_connection_info,
            target_connection_info)

    task_properties_params = {'input': task_input}

    return task_properties_type(**task_properties_params)


def get_scenario_type(source_platform, target_platform, task_type=""):
    if source_platform == "sql" and target_platform == "sqldb":
        scenario_type = ScenarioType.sql_sqldb_offline if not task_type or "offline" in task_type else \
            ScenarioType.unknown
    elif source_platform == "mysql" and target_platform == "azuredbformysql":
        scenario_type = ScenarioType.mysql_azuremysql_online if not task_type or "online" in task_type else \
            ScenarioType.unknown
    elif source_platform == "postgresql" and target_platform == "azuredbforpostgresql":
        scenario_type = ScenarioType.postgres_azurepostgres_online if not task_type or "online" in task_type else \
            ScenarioType.unknown
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
