# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.mgmt.appconfiguration.models import ConfigurationStoreUpdateParameters

from ._utils import resolve_resource_group, user_confirmation


def create_configstore(client, resource_group_name, name, location):
    return client.create(resource_group_name, name, location.lower())


def delete_configstore(cmd, client, name, resource_group_name=None, yes=False):
    if resource_group_name is None:
        resource_group_name, _ = resolve_resource_group(cmd, name)
    confirmation_message = "Are you sure you want to delete the App Configuration: {}".format(
        name)
    user_confirmation(confirmation_message, yes)
    return client.delete(resource_group_name, name)


def list_configstore(client, resource_group_name=None):
    response = client.list() if resource_group_name is None else client.list_by_resource_group(
        resource_group_name)
    return response


def show_configstore(cmd, client, name, resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_resource_group(cmd, name)
    return client.get(resource_group_name, name)


def configstore_update_get():
    return ConfigurationStoreUpdateParameters()


def configstore_update_set(cmd,
                           client,
                           parameters,
                           name,
                           resource_group_name=None):
    if resource_group_name is None:
        resource_group_name, _ = resolve_resource_group(cmd, name)

    return client.update(resource_group_name=resource_group_name,
                         config_store_name=name,
                         tags=parameters.tags)


def configstore_update_custom(instance, tags=None):
    if tags is not None:
        instance.tags = tags
    return instance


def list_credential(cmd, client, name, resource_group_name=None):
    resource_group_name, endpoint = resolve_resource_group(cmd, name)
    credentials = client.list_keys(resource_group_name, name)
    augmented_credentials = []

    for credentail in credentials:
        augmented_credential = __convert_api_key_to_json(credentail, endpoint)
        augmented_credentials.append(augmented_credential)
    return augmented_credentials


def regenerate_credential(cmd, client, name, id_, resource_group_name=None):
    resource_group_name, endpoint = resolve_resource_group(cmd, name)
    credentail = client.regenerate_key(resource_group_name, name, id_)
    return __convert_api_key_to_json(credentail, endpoint)


def __convert_api_key_to_json(credentail, endpoint):
    augmented_credential = {}
    augmented_credential['id'] = credentail.id
    augmented_credential['name'] = credentail.name
    augmented_credential['value'] = credentail.value
    augmented_credential['lastModified'] = credentail.last_modified
    augmented_credential['readOnly'] = credentail.read_only
    augmented_credential['connectionString'] = 'Endpoint=' + \
        endpoint + ';Id=' + credentail.id + ';Secret=' + credentail.value
    return augmented_credential
