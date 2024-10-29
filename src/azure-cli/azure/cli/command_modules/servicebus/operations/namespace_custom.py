# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.servicebus.constants import SYSTEM
from azure.cli.command_modules.servicebus.constants import SYSTEMUSER
from azure.cli.command_modules.servicebus.constants import USER


def create_keyvault_object(col):
    vault_object = {}
    if 'userAssignedIdentity' in col['identity']:
        vault_object['user_assigned_identity'] = col['identity']['userAssignedIdentity']

    vault_object.update({
        "key_name": col['keyName'],
        "key_vault_uri": col['keyVaultUri'],
        "key_version": col['keyVersion']
    })
    return vault_object


def create_replica_location_object(col):
    replica_location_object = {}
    replica_location_object.update({
        "location_name": col['locationName'],
        "role_type": col['roleType']
    })
    if 'clusterArmId' in col:
        replica_location_object.update({
            "cluster_arm_id": col['clusterArmId']
        })
    return replica_location_object


def create_servicebus_namespace(cmd, resource_group_name, namespace_name, location=None, tags=None, sku='Standard',
                                capacity=None, zone_redundant=None, mi_user_assigned=None,
                                mi_system_assigned=None, encryption_config=None, minimum_tls_version=None,
                                disable_local_auth=None, alternate_name=None, public_network_access=None,
                                require_infrastructure_encryption=None, premium_messaging_partitions=None,
                                max_replication_lag_duration_in_seconds=None,
                                geo_data_replication_config=None
                                ):

    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Create
    user_assigned_identity = {}
    command_args_dict = {}
    identity_type = "None"
    command_args_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "tags": tags,
        "sku": {
            "name": sku,
            "capacity": capacity,
            "tier": sku
        },
        "minimum_tls_version": minimum_tls_version,
        "location": location,
        "zone_redundant": zone_redundant,
        "disable_local_auth": disable_local_auth,
        "alternate_name": alternate_name,
        "public_network_access": public_network_access,
        "premium_messaging_partitions": premium_messaging_partitions
    }

    if mi_system_assigned:
        identity_type = SYSTEM
        command_args_dict.update({
            "identity": {
                "type": identity_type,
                "user_assigned_identities": None
            }
        })

    if mi_user_assigned:
        if mi_system_assigned:
            identity_type = SYSTEMUSER
        else:
            identity_type = USER
        for val in mi_user_assigned:
            user_assigned_identity[val] = {}
        command_args_dict.update({"identity": {
            "type": identity_type,
            "user_assigned_identities": user_assigned_identity
        }})

    if encryption_config:
        command_args_dict.update({"encryption": {
            "key_vault_properties": encryption_config,
            "key_source": "Microsoft.KeyVault",
            "require_infrastructure_encryption": require_infrastructure_encryption
        }})

    list_replication_object = []
    if geo_data_replication_config:
        for val in geo_data_replication_config:
            list_replication_object.append(val)
        command_args_dict.update({
            "geo_data_replication": {
                "locations": list_replication_object,
                "max_replication_lag_duration_in_seconds": max_replication_lag_duration_in_seconds
            }
        })

    return Create(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)


def cli_add_encryption(cmd, resource_group_name, namespace_name, encryption_config,
                       require_infrastructure_encryption=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show

    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    key_vault_object = []
    for col in encryption_config:
        key_vault_object.append(col)

    if 'encryption' in servicebusnm:
        for col in servicebusnm['encryption']['keyVaultProperties']:
            vault_object = create_keyvault_object(col)
            if vault_object not in key_vault_object:
                key_vault_object.append(vault_object)
        if require_infrastructure_encryption is None:
            require_infrastructure_encryption = servicebusnm['encryption']['requireInfrastructureEncryption']

    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "encryption": {
            "key_source": "Microsoft.KeyVault",
            "key_vault_properties": key_vault_object,
            "require_infrastructure_encryption": require_infrastructure_encryption
        }
    })


def cli_remove_encryption(cmd, resource_group_name, namespace_name, encryption_config):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show

    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })

    key_vault_object = []

    for col in servicebusnm['encryption']['keyVaultProperties']:
        vault_object = create_keyvault_object(col)
        key_vault_object.append(vault_object)
    for col in encryption_config:
        if col in key_vault_object:
            key_vault_object.remove(col)
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "encryption": {
            "require_infrastructure_encryption": servicebusnm['encryption']['requireInfrastructureEncryption'],
            "key_vault_properties": key_vault_object,
            "key_source": "Microsoft.KeyVault"
        }
    })


def cli_add_identity(cmd, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show

    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })

    if 'identity' not in servicebusnm:
        servicebusnm['identity'] = {
            "type": "None",
            "userAssignedIdentities": None
        }

    identity_type = servicebusnm['identity']['type']
    if system_assigned:
        if identity_type == USER:
            identity_type = SYSTEMUSER
        elif identity_type == "None":
            identity_type = SYSTEM

    if user_assigned:
        if identity_type == SYSTEM:
            identity_type = SYSTEMUSER
        else:
            identity_type = USER
        user_assigned_identity = {}
        for col in user_assigned:
            user_assigned_identity[col] = {}

        if 'userAssignedIdentities' in servicebusnm['identity']:
            if servicebusnm['identity']['userAssignedIdentities'] is None:
                servicebusnm['identity']['userAssignedIdentities'] = user_assigned_identity
            else:
                servicebusnm['identity']['userAssignedIdentities'].update(user_assigned_identity)
        else:
            servicebusnm['identity'] = {
                'userAssignedIdentities': user_assigned_identity,
                'type': identity_type
            }
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "identity": {
            "type": identity_type,
            "user_assigned_identities": servicebusnm['identity']['userAssignedIdentities']
        }
    })


def cli_remove_identity(cmd, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show

    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })

    identity_type = servicebusnm['identity']['type']
    if system_assigned:
        if identity_type == SYSTEM:
            identity_type = "None"
        if identity_type == SYSTEMUSER:
            identity_type = USER

    if user_assigned:
        if servicebusnm['identity']['userAssignedIdentities']:
            for x in user_assigned:
                servicebusnm['identity']['userAssignedIdentities'].pop(x)
            if identity_type == USER:
                if len(servicebusnm['identity']['userAssignedIdentities']) == 0:
                    identity_type = "None"
                    servicebusnm['identity']['userAssignedIdentities'] = None
            if identity_type == SYSTEMUSER:
                if len(servicebusnm['identity']['userAssignedIdentities']) == 0:
                    identity_type = "SystemAssigned"
                    servicebusnm['identity']['userAssignedIdentities'] = None

    command_args = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "identity": {
            "type": identity_type
        }
    }

    if 'userAssignedIdentities' in servicebusnm['identity']:
        command_args["identity"].update({
            "user_assigned_identities": servicebusnm['identity']['userAssignedIdentities']
        })
    return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args)


def sb_rule_create(cmd, resource_group_name, namespace_name, topic_name, subscription_name, rule_name,
                   action_sql_expression=None, action_compatibility_level=None, correlation_id=None,
                   action_requires_preprocessing=None, reply_to=None, label=None, session_id=None,
                   filter_sql_expression=None, filter_requires_preprocessing=None, reply_to_session_id=None,
                   message_id=None, to=None, content_type=None, requires_preprocessing=None,
                   filter_type=None, tags=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.topic.subscription.rule import Create
    command_arg_dict = {}
    command_arg_dict.update({
        'resource_group': resource_group_name,
        'namespace_name': namespace_name,
        'topic_name': topic_name,
        'subscription_name': subscription_name,
        'rule_name': rule_name,
        'action_sql_expression': action_sql_expression,
        'action_compatibility_level': action_compatibility_level,
        'action_requires_preprocessing': action_requires_preprocessing,
        'filter_type': filter_type
    })

    if filter_type == 'SqlFilter' or filter_type is None:
        command_arg_dict.update({
            'filter_sql_expression': filter_sql_expression,
            'filter_requires_preprocessing': filter_requires_preprocessing
        })

    if filter_type == 'CorrelationFilter':
        command_arg_dict.update({
            'properties': tags,
            'correlation_id': correlation_id,
            'to': to,
            'message_id': message_id,
            'reply_to': reply_to,
            'correlation_filter_property': tags,
            'session_id': session_id,
            'reply_to_session_id': reply_to_session_id,
            'content_type': content_type,
            'requires_preprocessing': requires_preprocessing,
            'label': label
        })
    return Create(cli_ctx=cmd.cli_ctx)(command_args=command_arg_dict)


def approve_private_endpoint_connection(cmd, resource_group_name, namespace_name,
                                        private_endpoint_connection_name, description=None):

    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.private_endpoint_connection import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.private_endpoint_connection import Show

    private_endpoint_connection = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "private_endpoint_connection_name": private_endpoint_connection_name
    })
    if private_endpoint_connection["privateLinkServiceConnectionState"]["status"] != "Approved":
        command_args_dict = {
            "resource_group": resource_group_name,
            "namespace_name": namespace_name,
            "private_endpoint_connection_name": private_endpoint_connection_name,
            "description": description,
            "status": "Approved"
        }
        return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)

    return Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "private_endpoint_connection_name": private_endpoint_connection_name,
    })


def reject_private_endpoint_connection(cmd, resource_group_name, namespace_name, private_endpoint_connection_name,
                                       description=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.private_endpoint_connection import Update
    command_args_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "private_endpoint_connection_name": private_endpoint_connection_name,
        "description": description,
        "status": "Rejected"
    }
    return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)


def delete_private_endpoint_connection(cmd, resource_group_name, namespace_name, private_endpoint_connection_name,
                                       description=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace.private_endpoint_connection import Delete
    command_args_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "private_endpoint_connection_name": private_endpoint_connection_name,
        "description": description
    }
    return Delete(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)


def set_georecovery_alias(cmd, resource_group_name, namespace_name, alias,
                          partner_namespace, alternate_name=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.georecovery_alias import Create
    command_arg_dict = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "partner_namespace": partner_namespace,
        "alternate_name": alternate_name,
        "alias": alias
    }
    return Create(cli_ctx=cmd.cli_ctx)(command_args=command_arg_dict)


def cli_add_location(cmd, resource_group_name, namespace_name, geo_data_replication_config):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show

    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    location_object = []
    for col in geo_data_replication_config:
        location_object.append(col)

    if 'geoDataReplication' in servicebusnm:
        for col in servicebusnm['geoDataReplication']['locations']:
            replica_object = create_replica_location_object(col)
            if replica_object not in location_object:
                location_object.append(replica_object)

    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "locations": location_object
    })


def cli_remove_location(cmd, resource_group_name, namespace_name, geo_data_replication_config):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show

    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })

    replica_location_object = []

    for col in servicebusnm['geoDataReplication']['locations']:
        replica_object = create_replica_location_object(col)
        replica_location_object.append(replica_object)
    for col in geo_data_replication_config:
        if col in replica_location_object:
            replica_location_object.remove(col)
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "locations": replica_location_object
    })
