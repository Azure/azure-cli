# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def maps_account_create(client,
                        resource_group_name,
                        account_name,
                        location,
                        name,
                        tags=None,
                        kind=None,
                        disable_local_auth=None,
                        linked_resources=None,
                        type_=None,
                        user_assigned_identities=None):
    if kind is None:
        kind = "Gen1"
    if disable_local_auth is None:
        disable_local_auth = False
    maps_account = {}
    maps_account['tags'] = tags
    maps_account['location'] = location
    maps_account['kind'] = "Gen1" if kind is None else kind
    maps_account['properties'] = {}
    maps_account['properties']['disable_local_auth'] = False if disable_local_auth is None else disable_local_auth
    maps_account['properties']['linked_resources'] = linked_resources
    maps_account['identity'] = {}
    maps_account['identity']['type'] = type_
    maps_account['identity']['user_assigned_identities'] = user_assigned_identities
    maps_account['sku'] = {}
    maps_account['sku']['name'] = name
    return client.create_or_update(resource_group_name=resource_group_name,
                                   account_name=account_name,
                                   maps_account=maps_account)


def list_accounts(client, resource_group_name=None):
    # Retrieve accounts via subscription
    if resource_group_name is None:
        return client.list_by_subscription()
    # Retrieve accounts via resource group
    return client.list_by_resource_group(resource_group_name)


def maps_account_show(client,
                      resource_group_name,
                      account_name):
    return client.get(resource_group_name=resource_group_name,
                      account_name=account_name)


def maps_account_update(client,
                        resource_group_name,
                        account_name,
                        tags=None,
                        kind=None,
                        disable_local_auth=None,
                        linked_resources=None,
                        type_=None,
                        user_assigned_identities=None,
                        name=None):
    if kind is None:
        kind = "Gen1"
    if disable_local_auth is None:
        disable_local_auth = False
    maps_account_update_parameters = {}
    maps_account_update_parameters['tags'] = tags
    maps_account_update_parameters['kind'] = "Gen1" if kind is None else kind
    maps_account_update_parameters['disable_local_auth'] = False if disable_local_auth is None else disable_local_auth
    maps_account_update_parameters['linked_resources'] = linked_resources
    maps_account_update_parameters['identity'] = {}
    maps_account_update_parameters['identity']['type'] = type_
    maps_account_update_parameters['identity']['user_assigned_identities'] = user_assigned_identities
    maps_account_update_parameters['sku'] = {}
    maps_account_update_parameters['sku']['name'] = name
    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         maps_account_update_parameters=maps_account_update_parameters)


def maps_account_delete(client,
                        resource_group_name,
                        account_name):
    return client.delete(resource_group_name=resource_group_name,
                         account_name=account_name)


def maps_account_list_key(client,
                          resource_group_name,
                          account_name):
    return client.list_keys(resource_group_name=resource_group_name,
                            account_name=account_name)


def maps_account_regenerate_key(client,
                                resource_group_name,
                                account_name,
                                key_type):
    key_specification = {}
    key_specification['key_type'] = key_type
    return client.regenerate_keys(resource_group_name=resource_group_name,
                                  account_name=account_name,
                                  key_specification=key_specification)


def maps_map_list_operation(client):
    return client.list_operations()


def maps_creator_list(client,
                      resource_group_name,
                      account_name):
    return client.list_by_account(resource_group_name=resource_group_name,
                                  account_name=account_name)


def maps_creator_show(client,
                      resource_group_name,
                      account_name,
                      creator_name):
    return client.get(resource_group_name=resource_group_name,
                      account_name=account_name,
                      creator_name=creator_name)


def maps_creator_create(client,
                        resource_group_name,
                        account_name,
                        creator_name,
                        location,
                        storage_units,
                        tags=None):
    creator_resource = {}
    creator_resource['tags'] = tags
    creator_resource['location'] = location
    creator_resource['properties'] = {}
    creator_resource['properties']['storage_units'] = storage_units
    return client.create_or_update(resource_group_name=resource_group_name,
                                   account_name=account_name,
                                   creator_name=creator_name,
                                   creator_resource=creator_resource)


def maps_creator_update(client,
                        resource_group_name,
                        account_name,
                        creator_name,
                        tags=None,
                        storage_units=None):
    creator_update_parameters = {}
    creator_update_parameters['tags'] = tags
    creator_update_parameters['storage_units'] = storage_units
    return client.update(resource_group_name=resource_group_name,
                         account_name=account_name,
                         creator_name=creator_name,
                         creator_update_parameters=creator_update_parameters)


def maps_creator_delete(client,
                        resource_group_name,
                        account_name,
                        creator_name):
    return client.delete(resource_group_name=resource_group_name,
                         account_name=account_name,
                         creator_name=creator_name)