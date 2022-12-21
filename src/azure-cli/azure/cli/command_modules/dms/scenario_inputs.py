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

from azure.cli.core.azclierror import ValidationError


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
    migration_level_settings = {}
    make_source_server_read_only = False
    additional_properties = {}
    selected_databases = []

    if not isinstance(database_options_json, dict):
        raise ValidationError('Format of the database option file is wrong')

    if 'selected_databases' not in database_options_json:
        raise ValidationError('Database option file should contain atleast one selected database for migration')
    selected_databases = database_options_json.get('selected_databases')

    for database in selected_databases:
        if not isinstance(database, dict):
            raise ValidationError('Format of the selected database file is wrong')
        if 'name' not in database:
            raise ValidationError('Selected database should have a name')
        if 'target_database_name' not in database:
            raise ValidationError('Selected database should have a target_database_name')
        if 'table_map' in database and (not isinstance(database.get('table_map'), dict) or
                                        len(database.get('table_map')) == 0):
            raise ValidationError('Table map should be dictionary and non empty, to select all tables remove table_map')
        database_options.append(
            MigrateMySqlAzureDbForMySqlOfflineDatabaseInput(
                name=database.get('name', None),
                target_database_name=database.get('target_database_name', None),
                table_map=database.get('table_map', None)))

    if 'migration_level_settings' in database_options_json and \
            (not isinstance(database_options_json, dict) or len(
                database_options_json.get('migration_level_settings')) == 0):
        raise ValidationError('migration_level_settings have wrong format or is empty')

    if isinstance(database_options_json, dict):
        if 'migration_level_settings' in database_options_json:
            migration_level_settings = database_options_json.get('migration_level_settings')

        if 'make_source_server_read_only' in database_options_json:
            make_source_server_read_only = database_options_json.get('make_source_server_read_only')

        if 'enable_consistent_backup' in database_options_json:
            enable_consistent_backup = database_options_json.get('enable_consistent_backup')
            migration_level_settings['enableConsistentBackup'] = enable_consistent_backup

        if 'migrate_all_views' in database_options_json:
            additional_properties['migrateAllViews'] = database_options_json.get('migrate_all_views')

        if 'migrate_all_triggers' in database_options_json:
            additional_properties['migrateAllTriggers'] = database_options_json.get('migrate_all_triggers')

        if 'migrate_all_events' in database_options_json:
            additional_properties['migrateAllEvents'] = database_options_json.get('migrate_all_events')

        if 'migrate_all_routines' in database_options_json:
            additional_properties['migrateAllRoutines'] = database_options_json.get('migrate_all_routines')

        if 'migrate_all_tables_schema' in database_options_json:
            additional_properties['migrateAllTablesSchema'] = database_options_json.get('migrate_all_tables_schema')

        if 'migrate_user_system_tables' in database_options_json:
            additional_properties['migrateUserSystemTables'] = database_options_json.get('migrate_user_system_tables')

    task_input = MigrateMySqlAzureDbForMySqlOfflineTaskInput(source_connection_info=source_connection_info,
                                                             target_connection_info=target_connection_info,
                                                             selected_databases=database_options,
                                                             optional_agent_settings=migration_level_settings,
                                                             make_source_server_read_only=make_source_server_read_only)

    if additional_properties:
        task_input.additional_properties = additional_properties
        task_input.enable_additional_properties_sending()

    return task_input
