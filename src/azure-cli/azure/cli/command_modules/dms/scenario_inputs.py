# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.datamigration.models import (MigrateSqlServerSqlDbTaskInput,
                                             MigrateSqlServerSqlDbDatabaseInput,
                                             MigrationValidationOptions,
                                             MigratePostgreSqlAzureDbForPostgreSqlSyncTaskInput,
                                             MigratePostgreSqlAzureDbForPostgreSqlSyncDatabaseInput,
                                             MigratePostgreSqlAzureDbForPostgreSqlSyncDatabaseTableInput,
                                             MigrateMySqlAzureDbForMySqlOfflineTaskInput,
                                             MigrateMySqlAzureDbForMySqlOfflineDatabaseInput)


def get_migrate_sql_to_sqldb_offline_input(database_options_json,
                                           source_connection_info,
                                           target_connection_info,
                                           enable_schema_validation,
                                           enable_data_integrity_validation,
                                           enable_query_analysis_validation):
    database_options = []

    for d in database_options_json:
        database_options.append(
            MigrateSqlServerSqlDbDatabaseInput(
                name=d.get('name', None),
                target_database_name=d.get('target_database_name', None),
                make_source_db_read_only=d.get('make_source_db_read_only', None),
                table_map=d.get('table_map', None)))

    validation_options = MigrationValidationOptions(enable_schema_validation=enable_schema_validation,
                                                    enable_data_integrity_validation=enable_data_integrity_validation,
                                                    enable_query_analysis_validation=enable_query_analysis_validation)

    return MigrateSqlServerSqlDbTaskInput(source_connection_info=source_connection_info,
                                          target_connection_info=target_connection_info,
                                          selected_databases=database_options,
                                          validation_options=validation_options)


def get_migrate_postgresql_to_azuredbforpostgresql_sync_input(database_options_json,
                                                              source_connection_info,
                                                              target_connection_info):
    database_options = []

    for d in database_options_json:
        s_t = d.get('selectedTables', None)
        t = None if s_t is None else [MigratePostgreSqlAzureDbForPostgreSqlSyncDatabaseTableInput(name=t) for t in s_t]
        database_options.append(
            MigratePostgreSqlAzureDbForPostgreSqlSyncDatabaseInput(
                name=d.get('name', None),
                target_database_name=d.get('target_database_name', None),
                migration_setting=d.get('migrationSetting', None),
                source_setting=d.get('sourceSetting', None),
                target_setting=d.get('targetSetting', None),
                selected_tables=t))

    return MigratePostgreSqlAzureDbForPostgreSqlSyncTaskInput(source_connection_info=source_connection_info,
                                                              target_connection_info=target_connection_info,
                                                              selected_databases=database_options)


def get_migrate_mysql_to_azuredbformysql_offline_input(database_options_json,
                                                       source_connection_info,
                                                       target_connection_info):
    database_options = []
    optional_agent_settings = {}
    make_source_server_read_only = False

    for d in database_options_json:
        database_options.append(
            MigrateMySqlAzureDbForMySqlOfflineDatabaseInput(
                name=d.get('name', None),
                target_database_name=d.get('target_database_name', None),
                table_map=d.get('table_map', None)))

    if isinstance(database_options_json, dict):
        optional_agent_settings = database_options_json.get('optional_agent_settings', None)
        source_setting = database_options_json.get('sourceSetting', None)
        if source_setting is not None and isinstance(source_setting, dict):
            make_source_server_read_only = source_setting.get('make_source_server_read_only', False)

    return MigrateMySqlAzureDbForMySqlOfflineTaskInput(source_connection_info=source_connection_info,
                                                       target_connection_info=target_connection_info,
                                                       selected_databases=database_options,
                                                       optional_agent_settings=optional_agent_settings,
                                                       make_source_server_read_only=make_source_server_read_only)
