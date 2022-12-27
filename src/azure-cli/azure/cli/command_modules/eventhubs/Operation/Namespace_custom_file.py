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
    user_assigned = {}
    a = "None"
    tier = sku
    if mi_system_assigned:
        a = "SystemAssigned"
    if mi_user_assigned:
        if mi_system_assigned:
            a = "SystemAssigned, UserAssigned"
        else:
            a = "UserAssigned"
        for col in mi_user_assigned:
            print(col)
            user_assigned[col] = {}
        return Create(cli_ctx=cmd.cli_ctx)(command_args={
            "resource_group": resource_group_name,
            "namespace_name": namespace_name,
            "tags": tags,
            "sku": {
                "name": sku,
                "capacity": capacity,
                "tier": sku
            },
            "minimum_tls_version": minimum_tls_version,
            "maximum_throughput_units":maximum_throughput_units,
            "is_kafka_enabled":is_kafka_enabled,
            "is_auto_inflate_enabled": is_auto_inflate_enabled,
            "encryption": {
                "key_source": "Microsoft.KeyVault",
                "key_vault_properties": encryption_config
            },
            "location": location,
            "identity": {
                "type": a,
                "user_assigned_identities": user_assigned
            },
            "zone_redundant": zone_redundant,
            "private_endpoint_connection_name": private_endpoint_connection_name,
            "disable_local_auth": disable_local_auth,
            "alternate_name": alternate_name
        })
    else:
        return Create(cli_ctx=cmd.cli_ctx)(command_args={
            "resource_group": resource_group_name,
            "namespace_name": namespace_name,
            "tags": tags,
            "sku": {
                "name": sku,
                "capacity": capacity,
                "tier": sku
            },
            "maximum_throughput_units": maximum_throughput_units,
            "is_kafka_enabled": is_kafka_enabled,
            "minimum_tls_version": minimum_tls_version,
            "location": location,
            "is_auto_inflate_enabled":is_auto_inflate_enabled,
            "identity": {
                "type": a,
                "user_assigned_identities": mi_user_assigned
            },
            "zone_redundant": zone_redundant,
            "private_endpoint_connection_name": private_endpoint_connection_name,
            "disable_local_auth": disable_local_auth,
            "alternate_name": alternate_name
        })
def cli_add_encryption(cmd, resource_group_name, namespace_name, encryption_config):
    #namespace = client.get(resource_group_name, namespace_name)
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Update
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Create
    from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.namespace import Show
    eventhubsnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    print(eventhubsnm)
    if  eventhubsnm['encryption']:
        i=0
        print("hello")
        for col in encryption_config:
            cmod = {
                'userAssignedIdentity': encryption_config[i]['identity']['user_assigned_identity'],
                'keyName': encryption_config[i]['key_name'],
                'keyVaultUri': encryption_config[i]['key_vault_uri'],
                'keyVersion': encryption_config[i]['key_version']

            }
            if eventhubsnm['encryption']['keyVaultProperties']:
                eventhubsnm['encryption']['keyVaultProperties'].extend([cmod])
            else:
                eventhubsnm['encryption']['keyVaultProperties']= [cmod]
            i+=1
            #print([cmod])
        k = []
        i = 0
        print(eventhubsnm['encryption']['keyVaultProperties'])
        for col in eventhubsnm['encryption']['keyVaultProperties']:
            user = {
                "key_name": eventhubsnm['encryption']['keyVaultProperties'][i]['keyName'],
                "key_vault_uri": eventhubsnm['encryption']['keyVaultProperties'][i]['keyVaultUri'],
                "Key_version": eventhubsnm['encryption']['keyVaultProperties'][i]['keyVersion'],
                "user_assigned_identity": eventhubsnm['encryption']['keyVaultProperties'][i]['userAssignedIdentity']
            }
            print(user)
            k.append(user)
            i += 1
        print(k)
        return Update(cli_ctx=cmd.cli_ctx)(command_args={
            "resource_group": resource_group_name,
            "namespace_name": namespace_name,
            "encryption":{
                "key_source": "Microsoft.KeyVault",
                "key_vault_properties": k
            }
        })
    else:
        return Update(cli_ctx=cmd.cli_ctx)(command_args={
            "resource_group": resource_group_name,
            "namespace_name": namespace_name,
            "encryption":{
                "key_source":"Microsoft.KeyVault",
                "key_vault_properties":encryption_config
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

    from azure.cli.core import CLIError
    if eventhubsnm['encryption']['keyVaultProperties']:
        i=0
        for encryption_property in encryption_config:
            cmod = {
                'userAssignedIdentity': encryption_config[i]['identity']['user_assigned_identity'],
                'keyName': encryption_config[i]['key_name'],
                'keyVaultUri': encryption_config[i]['key_vault_uri'],
                'keyVersion': encryption_config[i]['key_version']

            }
            if cmod in eventhubsnm['encryption']['keyVaultProperties']:
                eventhubsnm['encryption']['keyVaultProperties'].remove(cmod)
    keys = []
    i=0
    for col in eventhubsnm['encryption']['keyVaultProperties']:
        user = {
            "key_name": eventhubsnm['encryption']['keyVaultProperties'][i]['keyName'],
            "key_vault_uri": eventhubsnm['encryption']['keyVaultProperties'][i]['keyVaultUri'],
            "Key_version": eventhubsnm['encryption']['keyVaultProperties'][i]['keyVersion'],
            "user_assigned_identity": eventhubsnm['encryption']['keyVaultProperties'][i]['userAssignedIdentity']
        }
        keys.append(user)
        i += 1
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "encryption":{
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
    print(eventhubsnm)
    if system_assigned:
        if eventhubsnm['identity']['type']=="UserAssigned":
            eventhubsnm['identity']['type']="UserAssigned, SystemAssigned"
        elif eventhubsnm['identity']['type']=="None":
            eventhubsnm['identity']['type'] ="SystemAssigned"
            print("help")
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
            print(user_assign)
            eventhubsnm['identity']={
                'userAssignedIdentities':user_assign,
                'type':a
            }
    #print(eventhubsnm['identity'])
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
    from azure.cli.core import CLIError

    if eventhubsnm['identity'] is None:
        raise CLIError('The namespace does not have identity enabled')
    dict = {}
    if system_assigned:
        if eventhubsnm['identity']['type']=="SystemAssigned":
            eventhubsnm['identity']['type'] ="None"
        if eventhubsnm['identity']['type']=="SystemAssigned, UserAssigned":
            eventhubsnm['identity']['type'] = "UserAssigned"
    if user_assigned:
        if eventhubsnm['identity']['type']=="UserAssigned":
            if eventhubsnm['identity']['userAssignedIdentities']:
                for x in user_assigned:
                    eventhubsnm['identity']['userAssignedIdentities'].pop(x)
                if len(eventhubsnm['identity']['userAssignedIdentities'])==0:
                    print("hello21")
                    eventhubsnm['identity']['type']="None"
                    eventhubsnm['identity']['userAssignedIdentities']=None
                    print("hello12")
        if eventhubsnm['identity']['type']=="SystemAssigned, UserAssigned":
            print("hello")
            if eventhubsnm['identity']['userAssignedIdentities']:
                for x in user_assigned:
                    eventhubsnm['identity']['userAssignedIdentities'].pop(x)
                if len(eventhubsnm['identity']['userAssignedIdentities'])==0:
                    eventhubsnm['identity']['type']="SystemAssigned"
                    eventhubsnm['identity']['userAssignedIdentities']=None
    if 'userAssignedIdentities' in eventhubsnm['identity']:
        dict={

            "resource_group": resource_group_name,
            "namespace_name": namespace_name,
            "identity":{
                "type":eventhubsnm['identity']['type'],
                "user_assigned_identities":eventhubsnm['identity']['userAssignedIdentities']
            }
        }
    else:
        print("hello")
        dict = {
            "resource_group": resource_group_name,
            "namespace_name": namespace_name,
            "identity": {
                "type": eventhubsnm['identity']['type']
            }
        }
    print(dict)
    return Update(cli_ctx=cmd.cli_ctx)(command_args=dict)