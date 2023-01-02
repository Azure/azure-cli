# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
def create_servicebus_namespace(cmd, resource_group_name, namespace_name, location=None, tags=None, sku='Standard',
                         capacity=None, zone_redundant=None,  tier='Standard', mi_user_assigned=None, mi_system_assigned=None,
                          encryption_config=None, minimum_tls_version=None,disable_local_auth = None,
                                private_endpoint_connection_name='enabled',alternate_name=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Create
    user_assign = {}
    dict1 = {}
    a = "None"
    print(encryption_config)
    dict1 = {
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
        "private_endpoint_connection_name": private_endpoint_connection_name,
        "disable_local_auth": disable_local_auth,
        "alternate_name": alternate_name
    }
    if mi_system_assigned:
        a = "SystemAssigned"
    if mi_user_assigned:
        if mi_system_assigned:
            a = "SystemAssigned, UserAssigned"
        else:
            a = "UserAssigned"

        for col in mi_user_assigned:
            user_assign[col] = {}
        dict2 = {
            "identity": {
                "type": a,
                "user_assigned_identities": user_assign
            },
        }
        dict1.update(dict2)
    else:
        dict2 = {
            "identity": {
                "type": a,
                "user_assigned_identities": None
            },
        }
        dict1.update(dict2)
    if encryption_config:
        dict3 = {
            "encryption": {
                "key_vault_properties": encryption_config,
                "key_source": "Microsoft.KeyVault"
            }
        }
        dict1.update(dict3)
    print(dict1)
    return Create(cli_ctx=cmd.cli_ctx)(command_args=dict1)
def cli_add_encryption(cmd, resource_group_name, namespace_name, encryption_config,require_infrastructure_encryption=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Create
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show
    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    keys = []
    for col in encryption_config:
        keys.append(col)
    if 'encryption' in servicebusnm:
        i = 0
        for col in servicebusnm['encryption']['keyVaultProperties']:
            user = {}
            if 'userAssignedIdentity' in servicebusnm['encryption']['keyVaultProperties'][i]['identity']:
                user['identity']={
                    'user_assigned_identity' : servicebusnm['encryption']['keyVaultProperties'][i]['identity']['userAssignedIdentity']
                }
            user["key_name"] = servicebusnm['encryption']['keyVaultProperties'][i]['keyName']
            user["key_vault_uri"] = servicebusnm['encryption']['keyVaultProperties'][i]['keyVaultUri']
            user["key_version"] = servicebusnm['encryption']['keyVaultProperties'][i]['keyVersion']
            i = i + 1
            if user not in keys:
                keys.append(user)
        if require_infrastructure_encryption is None:
            require_infrastructure_encryption = servicebusnm['encryption']['requireInfrastructureEncryption']
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "encryption": {
            "key_source": "Microsoft.KeyVault",
            "key_vault_properties": keys,
            "require_infrastructure_encryption": require_infrastructure_encryption
        }
    })
def cli_remove_encryption(cmd,resource_group_name, namespace_name, encryption_config):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Create
    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    keys = []
    k = 0
    for col in servicebusnm['encryption']['keyVaultProperties']:
        user = {}
        if 'userAssignedIdentity' in servicebusnm['encryption']['keyVaultProperties'][k]['identity']:
            user['identity']={
                'user_assigned_identity' :servicebusnm['encryption']['keyVaultProperties'][k]['identity']['userAssignedIdentity']
            }
        user["key_name"] = servicebusnm['encryption']['keyVaultProperties'][k]['keyName']
        user["key_vault_uri"] = servicebusnm['encryption']['keyVaultProperties'][k]['keyVaultUri']
        user["key_version"] = servicebusnm['encryption']['keyVaultProperties'][k]['keyVersion']
        keys.append(user)
        k = k + 1
    for col in encryption_config:
        if col in keys:
            keys.remove(col)
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "encryption":{
            "require_infrastructure_encryption":servicebusnm['encryption']['requireInfrastructureEncryption'],
            "key_vault_properties": keys,
            "key_source":"Microsoft.KeyVault"
        }
    })
def cli_add_identity(cmd, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Create
    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    from azure.cli.core import CLIError
    if 'identity' not in servicebusnm:
        servicebusnm['identity'] = {
            "type": "None",
            "userAssignedIdentities": None
        }
    if system_assigned:
        if servicebusnm['identity']['type'] == "UserAssigned":
            servicebusnm['identity']['type'] = "UserAssigned, SystemAssigned"
        elif servicebusnm['identity']['type'] == "None":
            servicebusnm['identity']['type'] = "SystemAssigned"
    if user_assigned:
        if servicebusnm['identity']['type'] == "SystemAssigned":
            a = "SystemAssigned, UserAssigned"
        else:
            a = "UserAssigned"
        servicebusnm['identity']['type'] = a
        user_assign = {}
        for col in user_assigned:
            user_assign[col] = {}
        if 'userAssignedIdentities' in servicebusnm['identity']:
            if servicebusnm['identity']['userAssignedIdentities'] is None:
                servicebusnm['identity']['userAssignedIdentities'] = user_assign
            else:
                servicebusnm['identity']['userAssignedIdentities'].update(user_assign)

        else:
            print(user_assign)
            servicebusnm['identity'] = {
                'userAssignedIdentities': user_assign,
                'type': a
            }
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "identity": {
            "type": servicebusnm['identity']['type'],
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
    from azure.cli.core import CLIError

    if servicebusnm['identity'] is None:
        raise CLIError('The namespace does not have identity enabled')
    dict = {}
    if system_assigned:
        if servicebusnm['identity']['type'] == "SystemAssigned":
            servicebusnm['identity']['type'] = "None"
        if servicebusnm['identity']['type'] == "SystemAssigned, UserAssigned":
            servicebusnm['identity']['type'] = "UserAssigned"
    if user_assigned:
        if servicebusnm['identity']['userAssignedIdentities']:
            for x in user_assigned:
                servicebusnm['identity']['userAssignedIdentities'].pop(x)
            if servicebusnm['identity']['type'] == "UserAssigned":
                if len(servicebusnm['identity']['userAssignedIdentities']) == 0:
                    servicebusnm['identity']['type'] = "None"
                    servicebusnm['identity']['userAssignedIdentities'] = None
            if servicebusnm['identity']['type'] == "SystemAssigned, UserAssigned":
                if len(servicebusnm['identity']['userAssignedIdentities']) == 0:
                    servicebusnm['identity']['type'] = "SystemAssigned"
                    servicebusnm['identity']['userAssignedIdentities'] = None
    dict={}
    dict["resource_group"]=resource_group_name
    dict["namespace_name"]=namespace_name
    if 'userAssignedIdentities' in servicebusnm['identity']:
        dict["identity"]= {
                "type": servicebusnm['identity']['type'],
                "user_assigned_identities": servicebusnm['identity']['userAssignedIdentities']
        }
    else:
        dict["identity"]= {
                "type": servicebusnm['identity']['type']
            }
    return Update(cli_ctx=cmd.cli_ctx)(command_args=dict)