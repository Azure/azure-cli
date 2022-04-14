# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_sql_management_client(cli_ctx):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.sql import SqlManagementClient
    from msrest.authentication import Authentication
    from os import getenv

    # Allow overriding SQL resource manager URI using environment variable
    # for testing purposes. Subscription id is also determined by environment
    # variable.
    sql_rm_override = getenv('_AZURE_CLI_SQL_RM_URI')
    if sql_rm_override:
        return SqlManagementClient(
            subscription_id=getenv('_AZURE_CLI_SQL_SUB_ID'),
            base_url=sql_rm_override,
            credentials=Authentication())  # No authentication

    # Normal production scenario.
    return get_mgmt_service_client(cli_ctx, SqlManagementClient)


def get_sql_capabilities_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).capabilities


def get_sql_databases_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).databases


def get_sql_database_operations_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).database_operations


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


def get_sql_servers_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).servers


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


def get_sql_managed_instance_azure_ad_administrators_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_instance_administrators


def get_sql_managed_instance_azure_ad_only_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_instance_azure_ad_only_authentications


def get_sql_managed_databases_operations(cli_ctx, _):
    return get_sql_management_client(cli_ctx).managed_databases


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
