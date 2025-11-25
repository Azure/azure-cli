# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.dms.validators import throw_if_not_dictionary, throw_if_not_list
from azure.cli.core.azclierror import ValidationError
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


def get_migrate_mysql_to_azuredbformysql_sync_input(database_options_json,
                                                    source_connection_info,
                                                    target_connection_info):
    return get_migrate_mysql_to_azuredbformysql_input(database_options_json,
                                                      source_connection_info,
                                                      target_connection_info,
                                                      has_schema_migration_options=True,
                                                      has_consistent_snapshot_options=True,
                                                      has_binlog_position=False)


def get_migrate_mysql_to_azuredbformysql_offline_input(database_options_json,
                                                       source_connection_info,
                                                       target_connection_info):
    return get_migrate_mysql_to_azuredbformysql_input(database_options_json,
                                                      source_connection_info,
                                                      target_connection_info,
                                                      has_schema_migration_options=True,
                                                      has_consistent_snapshot_options=True,
                                                      has_binlog_position=False)


def get_migrate_mysql_to_azuredbformysql_cdc_input(database_options_json,
                                                   source_connection_info,
                                                   target_connection_info):
    return get_migrate_mysql_to_azuredbformysql_input(database_options_json,
                                                      source_connection_info,
                                                      target_connection_info,
                                                      has_schema_migration_options=False,
                                                      has_consistent_snapshot_options=False,
                                                      has_binlog_position=True)


def get_migrate_mysql_to_azuredbformysql_input(database_options_json,
                                               source_connection_info,
                                               target_connection_info,
                                               has_schema_migration_options: bool,
                                               has_consistent_snapshot_options: bool,
                                               has_binlog_position: bool):
    database_options = []
    migration_level_settings = {}
    make_source_server_read_only = False
    migration_properties = {}
    migrate_full_server = False

    if not isinstance(database_options_json, dict):
        raise ValidationError('Format of the database option file is wrong')

    migrate_full_server = database_options_json.get('migrate_full_server', False)
    if migrate_full_server:
        set_optional(migration_properties, 'migrateFullServer', database_options_json, 'migrate_full_server')

    if ('selected_databases' not in database_options_json) and (not migrate_full_server):
        raise ValidationError('Database option file should contain at least one selected database for migration')

    selected_databases = database_options_json.get('selected_databases')

    if selected_databases is not None:
        for database in selected_databases:
            if not isinstance(database, dict):
                raise ValidationError('Format of the selected database file is wrong')
            if 'name' not in database:
                raise ValidationError('Selected database should have a name')
            if 'target_database_name' not in database:
                raise ValidationError('Selected database should have a target_database_name')
            if 'table_map' in database and (not isinstance(database.get('table_map'), dict) or
                                            len(database.get('table_map')) == 0):
                raise ValidationError(
                    'table_map should be dictionary and non empty, to select all tables remove table_map')

            db_input = create_db_input(database, has_schema_migration_options)
            database_options.append(db_input)

    set_optional(migration_properties, 'sourceServerResourceId', database_options_json, 'source_server_resource_id')
    set_optional(migration_properties, 'targetServerResourceId', database_options_json, 'target_server_resource_id')

    if 'migration_level_settings' in database_options_json:
        migration_level_settings = database_options_json.get('migration_level_settings')
        if not isinstance(migration_level_settings, dict):
            raise ValidationError('migration_level_settings should be a dictionary')

    if has_consistent_snapshot_options:
        make_source_server_read_only = database_options_json.get('make_source_server_read_only', False)
        set_optional(migration_level_settings, 'enableConsistentBackup', database_options_json,
                     'enable_consistent_backup')
        set_optional(migration_level_settings, 'enableConsistentBackupWithoutLocks', database_options_json,
                     'enable_consistent_backup_without_locks')

    if has_schema_migration_options:
        extract_schema_migration_options(migration_properties, database_options_json)

    if has_binlog_position:
        set_required(migration_properties, 'binLogInfo', database_options_json, 'binlog_info', throw_if_not_dictionary)

    task_input = MigrateMySqlAzureDbForMySqlOfflineTaskInput(source_connection_info=source_connection_info,
                                                             target_connection_info=target_connection_info,
                                                             selected_databases=database_options,
                                                             optional_agent_settings=migration_level_settings,
                                                             make_source_server_read_only=make_source_server_read_only)

    if len(migration_properties) > 0:
        task_input.additional_properties = migration_properties
        task_input.enable_additional_properties_sending()

    return task_input


def extract_schema_migration_options(migration_properties, database_options_json):
    set_optional(migration_properties, 'migrateAllViews', database_options_json, 'migrate_all_views')
    set_optional(migration_properties, 'migrateAllTriggers', database_options_json, 'migrate_all_triggers')
    set_optional(migration_properties, 'migrateAllEvents', database_options_json, 'migrate_all_events')
    set_optional(migration_properties, 'migrateAllRoutines', database_options_json, 'migrate_all_routines')
    set_optional(migration_properties, 'migrateAllTablesSchema', database_options_json, 'migrate_all_tables_schema')
    set_optional(migration_properties, 'migrateUserSystemTables', database_options_json, 'migrate_user_system_tables')


def create_db_input(database, has_schema_migration_options):
    db_input = MigrateMySqlAzureDbForMySqlOfflineDatabaseInput(
        name=database.get('name'),
        target_database_name=database.get('target_database_name'),
        table_map=database.get('table_map'))

    if has_schema_migration_options:
        db_properties = {}
        set_optional(db_properties, 'tablesToMigrateSchema', database, 'tables_to_migrate_schema',
                     throw_if_not_dictionary)
        set_optional(db_properties, 'selectedViews', database, 'selected_views', throw_if_not_list)
        set_optional(db_properties, 'selectedTriggers', database, 'selected_triggers', throw_if_not_list)
        set_optional(db_properties, 'selectedRoutines', database, 'selected_routines', throw_if_not_list)
        set_optional(db_properties, 'selectedEvents', database, 'selected_events', throw_if_not_list)
        set_optional(db_properties,
                     'selectDatabaseForSchemaMigration',
                     database,
                     'select_database_for_schema_migration')

        if len(db_properties) > 0:
            db_input.additional_properties = db_properties
            db_input.enable_additional_properties_sending()

    return db_input


def set_optional(target: dict,
                 target_property: str,
                 source: dict,
                 source_property: str,
                 validator: callable([any, str]) = None):
    if source_property in source:
        value = source[source_property]
        if validator is not None:
            validator(value, source_property)
        target[target_property] = value


def set_required(target: dict,
                 target_property: str,
                 source: dict,
                 source_property: str,
                 validator: callable([any, str]) = None):
    if source_property in source:
        set_optional(target, target_property, source, source_property, validator)
    else:
        raise ValidationError("'%s' attribute is required but it is not found in the input json" % source_property)
