# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.eventhubs.constants import SYSTEM
from azure.cli.command_modules.eventhubs.constants import SYSTEMUSER
from azure.cli.command_modules.eventhubs.constants import USER


def create_keyvault_object(col):
    vault_object = {}
    if 'userAssignedIdentity' in col:
        vault_object['user_assigned_identity'] = col['userAssignedIdentity']

    vault_object.update({
        "key_name": col['keyName'],
        "key_vault_uri": col['keyVaultUri'],
        "key_version": col['keyVersion']
    })
    return vault_object


def create_eventhub_namespace(cmd, resource_group_name, namespace_name, location=None, tags=None, sku='Standard',
                              capacity=None, mi_user_assigned=None, mi_system_assigned=False, zone_redundant=None,
                              encryption_config=None, minimum_tls_version=None, disable_local_auth=None,
                              maximum_throughput_units=None, require_infrastructure_encryption=None,
                              is_kafka_enabled=None, is_auto_inflate_enabled=None, alternate_name=None,
                              public_network_access=None, cluster_arm_id=None):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Create

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
        "enable_auto_inflate": is_auto_inflate_enabled,
        "maximum_throughput_units": maximum_throughput_units,
        "is_kafka_enabled": is_kafka_enabled,
        "zone_redundant": zone_redundant,
        "disable_local_auth": disable_local_auth,
        "alternate_name": alternate_name,
        "public_network_access": public_network_access,
        "cluster_arm_id": cluster_arm_id
    }

    if mi_system_assigned:
        identity_type = SYSTEM

    if mi_user_assigned:
        if mi_system_assigned:
            identity_type = SYSTEMUSER
        else:
            identity_type = USER
        for val in mi_user_assigned:
            user_assigned_identity[val] = {}
        command_args_dict.update({
            "identity": {
                "type": identity_type,
                "user_assigned_identities": user_assigned_identity
            }})
    else:
        command_args_dict.update({
            "identity": {
                "type": identity_type,
                "user_assigned_identities": None
            }
        })

    if encryption_config:
        command_args_dict.update({
            "encryption": {
                "key_vault_properties": encryption_config,
                "key_source": "Microsoft.KeyVault",
                "require_infrastructure_encryption": require_infrastructure_encryption
            }})

    return Create(cli_ctx=cmd.cli_ctx)(command_args=command_args_dict)


def cli_add_encryption(cmd, resource_group_name, namespace_name, encryption_config,
                       require_infrastructure_encryption=None):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Show

    eventhubsnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    key_vault_object = []
    for col in encryption_config:
        key_vault_object.append(col)

    if 'encryption' in eventhubsnm:
        for col in eventhubsnm['encryption']['keyVaultProperties']:
            vault_object = create_keyvault_object(col)
            if vault_object not in key_vault_object:
                key_vault_object.append(vault_object)
        if require_infrastructure_encryption is None:
            require_infrastructure_encryption = eventhubsnm['encryption']['requireInfrastructureEncryption']

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
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Show

    eventhubsnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })

    key_vault_object = []

    for col in eventhubsnm['encryption']['keyVaultProperties']:
        vault_object = create_keyvault_object(col)
        key_vault_object.append(vault_object)
    for col in encryption_config:
        if col in key_vault_object:
            key_vault_object.remove(col)
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "encryption": {
            "require_infrastructure_encryption": eventhubsnm['encryption']['requireInfrastructureEncryption'],
            "key_vault_properties": key_vault_object,
            "key_source": "Microsoft.KeyVault"
        }
    })


def cli_add_identity(cmd, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Show

    eventhubsnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    if 'identity' not in eventhubsnm:
        eventhubsnm['identity'] = {
            "type": "None",
            "userAssignedIdentities": None
        }

    identity_type = eventhubsnm['identity']['type']
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

        if 'userAssignedIdentities' in eventhubsnm['identity']:
            if eventhubsnm['identity']['userAssignedIdentities'] is None:
                eventhubsnm['identity']['userAssignedIdentities'] = user_assigned_identity
            else:
                eventhubsnm['identity']['userAssignedIdentities'].update(user_assigned_identity)
        else:
            eventhubsnm['identity'] = {
                'userAssignedIdentities': user_assigned_identity,
                'type': identity_type
            }
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "identity": {
            "type": identity_type,
            "user_assigned_identities": eventhubsnm['identity']['userAssignedIdentities']
        }
    })


def cli_remove_identity(cmd, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Show

    eventhubsnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })

    identity_type = eventhubsnm['identity']['type']
    if system_assigned:
        if identity_type == SYSTEM:
            identity_type = "None"
        if identity_type == SYSTEMUSER:
            identity_type = USER

    if user_assigned:
        if eventhubsnm['identity']['userAssignedIdentities']:
            for x in user_assigned:
                eventhubsnm['identity']['userAssignedIdentities'].pop(x)
            if identity_type == USER:
                if len(eventhubsnm['identity']['userAssignedIdentities']) == 0:
                    identity_type = "None"
                    eventhubsnm['identity']['userAssignedIdentities'] = None
            if identity_type == SYSTEMUSER:
                if len(eventhubsnm['identity']['userAssignedIdentities']) == 0:
                    identity_type = "SystemAssigned"
                    eventhubsnm['identity']['userAssignedIdentities'] = None

    command_args = {
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "identity": {
            "type": identity_type
        }
    }

    if 'userAssignedIdentities' in eventhubsnm['identity']:
        command_args["identity"].update({
            "user_assigned_identities": eventhubsnm['identity']['userAssignedIdentities']
        })
    return Update(cli_ctx=cmd.cli_ctx)(command_args=command_args)
