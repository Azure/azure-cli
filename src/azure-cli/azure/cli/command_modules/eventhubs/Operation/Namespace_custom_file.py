# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
def create_eventhub_namespace(cmd, resource_group_name, namespace_name, location=None, tags=None, sku='Standard',
                         capacity=None,  tier='Standard', mi_user_assigned=None, mi_system_assigned=False,
                          encryption_config=None, minimum_tls_version=None,disable_local_auth = None,
                         maximum_throughput_units=None,private_endpoint_connection_name='enabled',
                         require_infrastructure_encryption=None,is_kafka_enabled=None,
                              is_auto_inflate_enabled=None,alternate_name=None, zone_redundant=None):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Create
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
        "enable_auto_inflate": is_auto_inflate_enabled,
        "maximum_throughput_units":maximum_throughput_units,
        "is_kafka_enabled":is_kafka_enabled,
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
                "key_source": "Microsoft.KeyVault",
                "require_infrastructure_encryption":require_infrastructure_encryption
            }
        }
        dict1.update(dict3)
    print(dict1)
    return Create(cli_ctx=cmd.cli_ctx)(command_args=dict1)

def cli_add_encryption(cmd, resource_group_name, namespace_name, encryption_config,require_infrastructure_encryption=None):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Create
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Show
    eventhubsnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    keys=[]
    for col in encryption_config:
        keys.append(col)
    if 'encryption' in eventhubsnm:
        i=0
        for col in eventhubsnm['encryption']['keyVaultProperties']:
            user = {}
            if 'userAssignedIdentity' in eventhubsnm['encryption']['keyVaultProperties'][i]:
                user['user_assigned_identity'] = eventhubsnm['encryption']['keyVaultProperties'][i][
                    'userAssignedIdentity']
            user["key_name"] = eventhubsnm['encryption']['keyVaultProperties'][i]['keyName']
            user["key_vault_uri"] = eventhubsnm['encryption']['keyVaultProperties'][i]['keyVaultUri']
            user["Key_version"] = eventhubsnm['encryption']['keyVaultProperties'][i]['keyVersion']
            i=i+1
            if user not in keys:
                keys.append(user)
        if require_infrastructure_encryption is None:
            require_infrastructure_encryption= eventhubsnm['encryption']['requireInfrastructureEncryption']
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
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Show
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Create
    eventhubsnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    keys = []
    k = 0
    for col in eventhubsnm['encryption']['keyVaultProperties']:
        user = {}
        if 'userAssignedIdentity' in eventhubsnm['encryption']['keyVaultProperties'][k]:
            user['user_assigned_identity'] = eventhubsnm['encryption']['keyVaultProperties'][k]['userAssignedIdentity']
        user["key_name"] = eventhubsnm['encryption']['keyVaultProperties'][k]['keyName']
        user["key_vault_uri"] = eventhubsnm['encryption']['keyVaultProperties'][k]['keyVaultUri']
        user["key_version"] = eventhubsnm['encryption']['keyVaultProperties'][k]['keyVersion']
        keys.append(user)
        k=k+1
    for col in encryption_config:
        if col in keys:
            keys.remove(col)
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "encryption":{
            "require_infrastructure_encryption":eventhubsnm['encryption']['requireInfrastructureEncryption'],
            "key_vault_properties": keys,
            "key_source":"Microsoft.KeyVault"
        }
    })
def cli_add_identity(cmd, resource_group_name, namespace_name,system_assigned=None, user_assigned=None):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Show
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Create
    eventhubsnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    from azure.cli.core import CLIError
    if 'identity' not in eventhubsnm:
        eventhubsnm['identity'] = {
            "type":"None",
            "userAssignedIdentities":None
        }
    if system_assigned:
        if eventhubsnm['identity']['type']=="UserAssigned":
            eventhubsnm['identity']['type']="UserAssigned, SystemAssigned"
        elif eventhubsnm['identity']['type']=="None":
            eventhubsnm['identity']['type'] ="SystemAssigned"
    if user_assigned:
        if eventhubsnm['identity']['type']=="SystemAssigned":
            a="SystemAssigned, UserAssigned"
        else:
            a="UserAssigned"
        eventhubsnm['identity']['type']=a
        user_assign={}
        for col in user_assigned:
            user_assign[col]={}
        if 'userAssignedIdentities' in eventhubsnm['identity']:
            if eventhubsnm['identity']['userAssignedIdentities'] is None:
                eventhubsnm['identity']['userAssignedIdentities']=user_assign
            else:
                eventhubsnm['identity']['userAssignedIdentities'].update(user_assign)

        else:
            eventhubsnm['identity']={
                'userAssignedIdentities':user_assign,
                'type':a
            }
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "identity":{
            "type":eventhubsnm['identity']['type'],
            "user_assigned_identities":eventhubsnm['identity']['userAssignedIdentities']
        }
    })

def cli_remove_identity(cmd, resource_group_name, namespace_name, system_assigned=None, user_assigned=None):
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Show
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Create
    eventhubsnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    if eventhubsnm['identity'] is None:
        raise CLIError('The namespace does not have identity enabled')
    dict = {}
    if system_assigned:
        if eventhubsnm['identity']['type'] == "SystemAssigned":
            eventhubsnm['identity']['type'] = "None"
        if eventhubsnm['identity']['type'] == "SystemAssigned, UserAssigned":
            eventhubsnm['identity']['type'] = "UserAssigned"
    if user_assigned:
        if eventhubsnm['identity']['userAssignedIdentities']:
            for x in user_assigned:
                eventhubsnm['identity']['userAssignedIdentities'].pop(x)
            if eventhubsnm['identity']['type'] == "UserAssigned":
                if len(eventhubsnm['identity']['userAssignedIdentities']) == 0:
                    eventhubsnm['identity']['type'] = "None"
                    eventhubsnm['identity']['userAssignedIdentities'] = None
            if eventhubsnm['identity']['type'] == "SystemAssigned, UserAssigned":
                if len(eventhubsnm['identity']['userAssignedIdentities']) == 0:
                    eventhubsnm['identity']['type'] = "SystemAssigned"
                    eventhubsnm['identity']['userAssignedIdentities'] = None
    dict={}
    dict["resource_group"]=resource_group_name
    dict["namespace_name"]=namespace_name
    if 'userAssignedIdentities' in eventhubsnm['identity']:
        dict["identity"]= {
                "type": eventhubsnm['identity']['type'],
                "user_assigned_identities": eventhubsnm['identity']['userAssignedIdentities']
        }
    else:
        dict["identity"]= {
                "type": eventhubsnm['identity']['type']
            }
    return Update(cli_ctx=cmd.cli_ctx)(command_args=dict)