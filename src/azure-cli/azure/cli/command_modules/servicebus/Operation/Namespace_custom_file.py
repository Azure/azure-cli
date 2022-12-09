# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
def create_servicebus_namespace(cmd, resource_group_name, namespace_name, location=None, tags=None, sku='Standard',
                         capacity=None, zone_redundant=None,  tier='Standard', mi_user_assigned=None, mi_system_assigned=None,
                          encryption_config=None, minimum_tls_version=None,disable_local_auth = None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Create
    print(namespace_name)
    print(resource_group_name)
    user_assigned = {}
    a= None
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
        "sku":sku,
        "capacity": capacity,
        "tier":tier,
        "minimum_tls_version": minimum_tls_version,
        "encryption_config": encryption_config,
        "location":location,
        "user_assigned_identity": user_assigned,
        "identity_type":a,
        "zone_redundant":zone_redundant,
        "disable_local_auth":disable_local_auth
     })
def update_servicebus_namespace(cmd, resource_group_name, namespace_name, location=None, tags=None, sku='Standard',
                         capacity=None,  tier='Standard', mi_user_assigned=None, mi_system_assigned=None,
                          encryption_config=None, minimum_tls_version=None,disable_local_auth = None):
    from azure.cli.command_modules.servicebus.aaz.latest.servicebus.namespace import Create
    print(namespace_name)
    print(resource_group_name)
    user_assigned = {}
    a= None
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
        "sku":sku,
        "capacity": capacity,
        "tier":tier,
        "minimum_tls_version": minimum_tls_version,
        "key_vault_properties":encryption_config,
        "location":location,
        "user_assigned_identity": user_assigned,
        "identity_type":a,
        "zone_redundant":zone_redundant,
        "disable_local_auth":disable_local_auth
     })