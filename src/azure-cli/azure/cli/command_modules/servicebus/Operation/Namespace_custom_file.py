# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
def create_servicebus_namespace(cmd, resource_group_name, namespace_name, location=None, tags=None, sku='Standard',
                         capacity=None, zone_redundant=None,  tier='Standard', mi_user_assigned=None, mi_system_assigned=None,
                          encryption_config=None, minimum_tls_version=None,disable_local_auth = None,
                                private_endpoint_connection_name='enabled',alternate_name=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Create
    user_assigned = {}
    a= "None"
    tier = sku
    if mi_system_assigned:
        a="SystemAssigned"
    if mi_user_assigned:
        if mi_system_assigned:
            a="SystemAssigned, UserAssigned"
        else:
            a="UserAssigned"
        for col in mi_user_assigned:
            print(col)
            user_assigned[col]={}
        return Create(cli_ctx=cmd.cli_ctx)(command_args={
            "resource_group": resource_group_name,
            "namespace_name": namespace_name,
            "tags": tags,
            "sku":{
                "name":sku,
                "capacity":capacity,
                "tier":sku
            },
            "minimum_tls_version": minimum_tls_version,
            "encryption":{
            "key_source":"Microsoft.KeyVault",
            "key_vault_properties":encryption_config
            },
            "location":location,
            "identity":{
                "type":a,
                "user_assigned_identities":user_assigned
            },
            "zone_redundant":zone_redundant,
            "private_endpoint_connection_name":private_endpoint_connection_name,
            "disable_local_auth":disable_local_auth,
            "alternate_name":alternate_name
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
        "minimum_tls_version": minimum_tls_version,
        "location": location,
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
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Create
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show
    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    print(servicebusnm)
    if 'encryption' in servicebusnm:
        i=0
        for col in encryption_config:
            cmod = {
                'identity': {
                    'userAssignedIdentity': encryption_config[i]['identity']['user_assigned_identity']
                },
                'keyName': encryption_config[i]['key_name'],
                'keyVaultUri': encryption_config[i]['key_vault_uri'],
                'keyVersion': encryption_config[i]['key_version']

            }
            if servicebusnm['encryption']['keyVaultProperties']:
                servicebusnm['encryption']['keyVaultProperties'].extend([cmod])
            else:
                servicebusnm['encryption']['keyVaultProperties']= [cmod]
            i+=1
            print([cmod])
        keys=[]
        i=0
        for col in servicebusnm['encryption']['keyVaultProperties']:
            user = {
                "key_name":servicebusnm['encryption']['keyVaultProperties'][i]['keyName'],
                "key_vault_uri":servicebusnm['encryption']['keyVaultProperties'][i]['keyVaultUri'],
                "Key_version":servicebusnm['encryption']['keyVaultProperties'][i]['keyVersion'],
                "identity":{
                    "user_assigned_identity":servicebusnm['encryption']['keyVaultProperties'][i]['identity']['userAssignedIdentity']
                }
            }
            keys.append(user)
            i+=1
        print(keys)
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "encryption":{
            "key_source":"Microsoft.KeyVault",
            "key_vault_properties":keys
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

    from azure.cli.core import CLIError
    if servicebusnm['encryption']['keyVaultProperties']:
        print("hello123")
        i=0
        for encryption_property in encryption_config:
            cmod = {
                'identity': {
                    'userAssignedIdentity': encryption_config[i]['identity']['user_assigned_identity']
                },
                'keyName': encryption_config[i]['key_name'],
                'keyVaultUri': encryption_config[i]['key_vault_uri'],
                'keyVersion': encryption_config[i]['key_version']

            }
            if cmod in servicebusnm['encryption']['keyVaultProperties']:
                print(encryption_property)
                servicebusnm['encryption']['keyVaultProperties'].remove(cmod)
    keys = []
    i = 0
    #print(servicebusnm['encryption']['keyVaultProperties'])
    for col in servicebusnm['encryption']['keyVaultProperties']:
        user = {
            "key_name": servicebusnm['encryption']['keyVaultProperties'][i]['keyName'],
            "key_vault_uri": servicebusnm['encryption']['keyVaultProperties'][i]['keyVaultUri'],
            "Key_version": servicebusnm['encryption']['keyVaultProperties'][i]['keyVersion'],
            "identity": {
                "user_assigned_identity": servicebusnm['encryption']['keyVaultProperties'][i]['identity'][
                    'userAssignedIdentity']
            }
        }
        keys.append(user)
        i += 1
    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "encryption": {
            "key_source": "Microsoft.KeyVault",
            "key_vault_properties": keys
        }
    })
def cli_add_identity(cmd, resource_group_name, namespace_name, mi_system_assigned=None, mi_user_assigned=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Create
    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    from azure.cli.core import CLIError
    if servicebusnm['identity'] is None:
        servicebusnm['identity'] = {
            "type":None,
            "userAssignedIdentities":None
        }

    if mi_system_assigned:
        if servicebusnm['identity']['type']=="UserAssigned":
            servicebusnm['identity']['type']=="UserAssigned, SystemAssigned"
        elif servicebusnm['identity']['type']=="None":
            servicebusnm['identity']['type'] == "SystemAssigned"
    print(servicebusnm['identity']['userAssignedIdentities'])
    if mi_user_assigned:
        if servicebusnm['identity']['type']=="SystemAssigned":
            a="SystemAssigned, UserAssigned"
        else:
            a="UserAssigned"
        servicebusnm['identity']['type']=a
        user_assigned={}
        for col in mi_user_assigned:
            user_assigned[col]={}
        #identity_id.update(dict.fromkeys(user_assigned, default_user_identity))
        if servicebusnm['identity']['userAssignedIdentities'] is None:
            servicebusnm['identity']['userAssignedIdentities'].update(user_assigned)
        else:
            servicebusnm['identity']['userAssignedIdentities'].update(user_assigned)

    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "identity":{
            "type":servicebusnm['identity']['type'],
            "user_assigned_identities":servicebusnm['identity']['userAssignedIdentities']
        }
    })


def cli_remove_identity(cmd, resource_group_name, namespace_name, mi_system_assigned=None, mi_user_assigned=None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Update
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Show
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Create
    servicebusnm = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name
    })
    from azure.cli.core import CLIError

    if servicebusnm['identity'] is None:
        raise CLIError('The namespace does not have identity enabled')

    if mi_system_assigned:
        if servicebusnm['identity']['type']=="SystemAssigned":
            servicebusnm['identity']['type'] =None
        if servicebusnm['identity']['type']=="SystemAssigned, UserAssigned":
            servicebusnm['identity']['type'] = "UserAssigned"

    if mi_user_assigned:
        if servicebusnm['identity']['type']=="UserAssigned":
            if servicebusnm['identity']['userAssignedIdentities']:
                for x in mi_user_assigned:
                    servicebusnm['identity']['userAssignedIdentities'].pop(x)
                if len(servicebusnm['identity']['userAssignedIdentities'])==0:
                    print("hello21")
                    servicebusnm['identity']['type']="None"
                    servicebusnm['identity']['userAssignedIdentities']=None
                    print("hello12")
        if servicebusnm['identity']['type']=="SystemAssigned, UserAssigned":
            print("hello")
            if servicebusnm['identity']['userAssignedIdentities']:
                for x in mi_user_assigned:
                    servicebusnm['identity']['userAssignedIdentities'].pop(x)
                if len(servicebusnm['identity']['userAssignedIdentities'])==0:
                    servicebusnm['identity']['type']="SystemAssigned"
                    servicebusnm['identity']['userAssignedIdentities']=None

    return Update(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "namespace_name": namespace_name,
        "identity": {
            "type": servicebusnm['identity']['type'],
            "user_assigned_identities": servicebusnm['identity']['userAssignedIdentities']
        }
    })