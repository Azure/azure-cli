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
                                             MigrateMySqlAzureDbForMySqlOfflineDatabaseInput,
                                             MigrateMySqlAzureDbForMySqlSyncDatabaseInput,
                                             MigrateMySqlAzureDbForMySqlSyncTaskInput)

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


def get_migrate_mysql_to_azuredbformysql_sync_input(database_options_json,
                                                    source_connection_info,
                                                    target_connection_info):
    return get_migrate_mysql_to_azuredbformysql_input(database_options_json,
                                                      source_connection_info,
                                                      target_connection_info,
                                                      has_schema_migration_options=True,
                                                      has_consistent_snapshot_options=True,
                                                      requires_consistent_snapshot=True,
                                                      has_binlog_position=False)


def get_migrate_mysql_to_azuredbformysql_offline_input(database_options_json,
                                                       source_connection_info,
                                                       target_connection_info):
    return get_migrate_mysql_to_azuredbformysql_input(database_options_json,
                                                      source_connection_info,
                                                      target_connection_info,
                                                      has_schema_migration_options=True,
                                                      has_consistent_snapshot_options=True,
                                                      requires_consistent_snapshot=False,
                                                      has_binlog_position=False)


def get_migrate_mysql_to_azuredbformysql_cdc_input(database_options_json,
                                                   source_connection_info,
                                                   target_connection_info):
    return get_migrate_mysql_to_azuredbformysql_input(database_options_json,
                                                      source_connection_info,
                                                      target_connection_info,
                                                      has_schema_migration_options=False,
                                                      has_consistent_snapshot_options=False,
                                                      requires_consistent_snapshot=False,
                                                      has_binlog_position=True)


def get_migrate_mysql_to_azuredbformysql_input(database_options_json,
                                               source_connection_info,
                                               target_connection_info,
                                               has_schema_migration_options: bool,
                                               has_consistent_snapshot_options: bool,
                                               requires_consistent_snapshot: bool,
                                               has_binlog_position: bool):
    database_options = []
    migration_level_settings = {}
    make_source_server_read_only = False
    additional_properties = {}
    selected_databases = []

    if not isinstance(database_options_json, dict):
        raise ValidationError('Format of the database option file is wrong')

    if 'selected_databases' not in database_options_json:
        raise ValidationError('Database option file should contain at least one selected database for migration')

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
            raise ValidationError('table_map should be dictionary and non empty, to select all tables remove table_map')

        db_input = MigrateMySqlAzureDbForMySqlOfflineDatabaseInput(
            name=database.get('name', None),
            target_database_name=database.get('target_database_name', None),
            table_map=database.get('table_map', None))

        if has_schema_migration_options:
            tables_to_migrate_schema = database.get("tablesToMigrateSchema", {})
            if not isinstance(tables_to_migrate_schema, dict):
                raise ValidationError('tables_to_migrate_schema should be a dictionary')
            db_input.additional_properties = {"tablesToMigrateSchema": tables_to_migrate_schema}
            db_input.enable_additional_properties_sending()

        database_options.append(db_input)

    if 'migration_level_settings' in database_options_json:
        migration_level_settings = database_options_json.get('migration_level_settings')
        if not isinstance(migration_level_settings, dict):
            raise ValidationError('migration_level_settings should be a dictionary')

    if requires_consistent_snapshot:
        migration_level_settings['enableConsistentBackup'] = 'true'
    elif has_consistent_snapshot_options:
        if 'make_source_server_read_only' in database_options_json:
            make_source_server_read_only = database_options_json.get('make_source_server_read_only')
        if 'enable_consistent_backup' in database_options_json:
            migration_level_settings['enableConsistentBackup'] = database_options_json.get('enable_consistent_backup')

    if has_schema_migration_options:
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

    if has_binlog_position:
        binlog_info = additional_properties.get('binlog_info', {})
        if not isinstance(binlog_info, dict) or len(binlog_info) == 0:
            raise ValidationError("binlog_info should be a non-empty dictionary")
        additional_properties['binLogInfo'] = binlog_info

    task_input = MigrateMySqlAzureDbForMySqlOfflineTaskInput(source_connection_info=source_connection_info,
                                                             target_connection_info=target_connection_info,
                                                             selected_databases=database_options,
                                                             optional_agent_settings=migration_level_settings,
                                                             make_source_server_read_only=make_source_server_read_only)

    if len(additional_properties) > 0:
        task_input.additional_properties = additional_properties
        task_input.enable_additional_properties_sending()

    return task_input


def validate_keys_and_values_match(table_map: dict):
    renamed_tables = {s: t for s, t in table_map.items() if s != t}
    if len(renamed_tables) > 0:
        raise ValidationError(
            "All source and target table names should match. The following mismatches were found: " + str(renamed_tables))
