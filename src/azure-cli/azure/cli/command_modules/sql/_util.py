# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _normalize_model_key(key):
    return key.replace('_', '').lower()


def build_sdk_model(model_type, values):
    # SQL SDK 5.0 replaces msrest models with TypeSpec models. Preserve legacy CLI argument aliases:
    # a key matches a model attribute
    # by attribute name or by REST name (ignoring case and underscores), and keys that match nothing
    # (e.g. CLI-only arguments) or have a None value are skipped. The new SDK models are strict and
    # would otherwise raise on unknown keywords or serialize flattened properties at the wrong level.
    template = model_type()
    lookup = {}

    def _add(attr_name, rest_name):
        lookup.setdefault(_normalize_model_key(attr_name), attr_name)
        lookup.setdefault(_normalize_model_key(rest_name), attr_name)

    for attr_name, rest_field in template._attr_to_rest_field.items():  # pylint: disable=protected-access
        _add(attr_name, rest_field._rest_name)  # pylint: disable=protected-access

    properties_field = template._attr_to_rest_field.get('properties')  # pylint: disable=protected-access
    flattened = getattr(model_type, '_{}__flattened_items'.format(model_type.__name__), [])
    if properties_field is not None and flattened:
        properties = properties_field._class_type()  # pylint: disable=protected-access
        for attr_name, rest_field in properties._attr_to_rest_field.items():  # pylint: disable=protected-access
            if attr_name in flattened:
                _add(attr_name, rest_field._rest_name)  # pylint: disable=protected-access

    kwargs = {}
    for key, value in values.items():
        if value is None:
            continue
        attr_name = key if key in lookup.values() else lookup.get(_normalize_model_key(key))
        if attr_name:
            kwargs[attr_name] = value
    return model_type(**kwargs)


def _dict_to_sdk_model(method, parameters):
    # SQL SDK 5.0 sends dicts as raw JSON instead of applying msrest's attribute-to-REST-name mapping.
    # Build the declared model so CLI kwargs are nested under properties and use the correct REST names.
    import inspect
    import typing

    param = inspect.signature(method).parameters.get('parameters')
    if param is not None:
        for candidate in typing.get_args(param.annotation):
            if inspect.isclass(candidate) and candidate.__module__ == 'azure.mgmt.sql.models._models':
                return build_sdk_model(candidate, parameters)
    return parameters


class _SqlOperationsProxy:  # pylint: disable=too-few-public-methods
    # Keep legacy handlers that pass parameters=dict working without changing every request builder.
    def __init__(self, operations):
        self._operations = operations

    def __getattr__(self, name):
        attr = getattr(self._operations, name)
        if not callable(attr):
            return attr

        import functools

        @functools.wraps(attr)
        def _call(*args, **kwargs):
            if isinstance(kwargs.get('parameters'), dict):
                kwargs['parameters'] = _dict_to_sdk_model(attr, kwargs['parameters'])
            return attr(*args, **kwargs)

        return _call


class _SqlClientProxy:
    # Apply request-model conversion to every operation group, including cross-subscription clients.
    def __init__(self, client):
        self._client = client

    def __getattr__(self, name):
        attr = getattr(self._client, name)
        if name.startswith('_') or not hasattr(attr, '_client'):
            return attr
        return _SqlOperationsProxy(attr)

    def __enter__(self):
        self._client.__enter__()
        return self

    def __exit__(self, *exc_details):
        return self._client.__exit__(*exc_details)


def get_sql_management_client(cli_ctx, subscription_id=None, api_version=None):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.sql import SqlManagementClient
    from msrest.authentication import Authentication
    from os import getenv
    # An explicit version is needed only for the expanded-keys regression in the new default API.
    client_kwargs = {'api_version': api_version} if api_version is not None else {}

    # Allow overriding SQL resource manager URI using environment variable
    # for testing purposes. Subscription id is also determined by environment
    # variable.
    sql_rm_override = getenv('_AZURE_CLI_SQL_RM_URI')
    if sql_rm_override:
        return _SqlClientProxy(SqlManagementClient(
            subscription_id=getenv('_AZURE_CLI_SQL_SUB_ID'),
            base_url=sql_rm_override,
            credentials=Authentication(),
            **client_kwargs))  # No authentication

    # Cross-subscription scenario.
    if subscription_id is not None:
        return _SqlClientProxy(
            get_mgmt_service_client(cli_ctx, SqlManagementClient, subscription_id=subscription_id, **client_kwargs))

    # Normal production scenario.
    return _SqlClientProxy(get_mgmt_service_client(cli_ctx, SqlManagementClient, **client_kwargs))


def get_sql_capabilities_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).capabilities


def get_sql_databases_operations(cli_ctx, _, subscription_id=None):
    return get_sql_management_client(cli_ctx, subscription_id).databases


def get_sql_database_operations_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).database_operations


def get_sql_database_advanced_threat_protection_settings_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).database_advanced_threat_protection_settings


def get_sql_database_blob_auditing_policies_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).database_blob_auditing_policies


def get_sql_server_blob_auditing_policies_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).server_blob_auditing_policies


def get_sql_server_dev_ops_audit_settings_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).server_dev_ops_audit_settings


def get_sql_database_sensitivity_labels_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).sensitivity_labels


def get_sql_database_threat_detection_policies_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).database_security_alert_policies


def get_sql_database_transparent_data_encryptions_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).transparent_data_encryptions


def get_sql_database_usages_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).database_usages


def get_sql_elastic_pools_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).elastic_pools


def get_sql_elastic_pool_operations_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).elastic_pool_operations


def get_sql_encryption_protectors_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).encryption_protectors


def get_sql_managed_instance_encryption_protectors_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_instance_encryption_protectors


def get_sql_server_trust_groups_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).server_trust_groups


def get_sql_failover_groups_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).failover_groups


def get_sql_firewall_rules_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).firewall_rules


def get_sql_ipv6_firewall_rules_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).ipv6_firewall_rules


def get_sql_outbound_firewall_rules_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).outbound_firewall_rules


def get_sql_instance_pools_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).instance_pools


def get_sql_recommended_elastic_pools_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).recommended_elastic_pools


def get_sql_replication_links_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).replication_links


def get_sql_restorable_dropped_databases_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).restorable_dropped_databases


def get_sql_restorable_dropped_managed_databases_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).restorable_dropped_managed_databases


def get_sql_server_advanced_threat_protection_settings_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).server_advanced_threat_protection_settings


def get_sql_server_azure_ad_administrators_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).server_azure_ad_administrators


def get_sql_server_connection_policies_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).server_connection_policies


def get_sql_server_dns_aliases_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).server_dns_aliases


def get_sql_server_keys_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).server_keys


def get_sql_managed_instance_keys_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_instance_keys


def get_sql_servers_operations(cli_ctx, _, subscription_id=None):
    return get_sql_management_client(cli_ctx, subscription_id).servers


def get_sql_server_usages_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).server_usages


def get_sql_subscription_usages_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).subscription_usages


def get_sql_server_azure_ad_only_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).server_azure_ad_only_authentications


def get_sql_virtual_network_rules_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).virtual_network_rules


def get_sql_managed_instance_operations_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_instance_operations


def get_sql_managed_instances_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_instances


def get_sql_managed_instance_advanced_threat_protection_settings_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_instance_advanced_threat_protection_settings


def get_sql_managed_instance_azure_ad_administrators_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_instance_administrators


def get_sql_managed_instance_azure_ad_only_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_instance_azure_ad_only_authentications


def get_sql_managed_databases_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_databases


def get_sql_recoverable_managed_databases_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).recoverable_managed_databases


def get_sql_managed_database_advanced_threat_protection_settings_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_database_advanced_threat_protection_settings


def get_sql_backup_short_term_retention_policies_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).backup_short_term_retention_policies


def get_sql_managed_backup_short_term_retention_policies_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_backup_short_term_retention_policies


def get_sql_restorable_dropped_database_managed_backup_short_term_retention_policies_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_restorable_dropped_database_backup_short_term_retention_policies


def get_sql_virtual_clusters_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).virtual_clusters


def get_sql_instance_failover_groups_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).instance_failover_groups


def get_sql_managed_database_long_term_retention_policies_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_instance_long_term_retention_policies


def get_sql_managed_database_long_term_retention_backups_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).long_term_retention_managed_instance_backups


def get_sql_database_long_term_retention_policies_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).long_term_retention_policies


def get_sql_database_long_term_retention_backups_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).long_term_retention_backups


def get_sql_managed_database_restore_details_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_database_restore_details


def get_sql_database_ledger_digest_uploads_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).ledger_digest_uploads


def get_sql_database_encryption_protector_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).database_encryption_protectors


def get_sql_database_recoverable_databases_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).recoverable_databases


def get_sql_managed_database_ledger_digest_uploads_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_ledger_digest_uploads


def get_sql_managed_database_move_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_database_move_operations


def get_sql_deleted_servers_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).deleted_servers
