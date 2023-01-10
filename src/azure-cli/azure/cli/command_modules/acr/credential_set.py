# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger
from msrestazure.tools import is_valid_resource_id, parse_resource_id
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import InvalidArgumentValueError
from ._utils import validate_premium_registry, get_registry_by_name



def acr_cred_set_show(cmd,
                   client,
                   registry_name,
                   name):

    _, rg = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)

    return client.credential_sets.get(resource_group_name=rg,
                                  registry_name=registry_name,
                                  credential_set_name=name)

def acr_cred_set_list(cmd,
                   client,
                   registry_name):
    _, rg = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)
    return client.credential_sets.list(resource_group_name=rg,
                                  registry_name=registry_name)

def acr_cred_set_delete(cmd,
                   client,
                   registry_name,
                   name):
    _, rg = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)
    return client.credential_sets.begin_delete(resource_group_name=rg,
                                  registry_name=registry_name,
                                  credential_set_name=name)

def acr_cred_set_create(cmd,
                     client,
                     registry_name,
                     name,
                     password_id,
                     username_id,
                     login_server):

    registry, rg = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)

    credential_set_create_parameters = {
                    "name": name,  # Optional. The name of the resource.
                    "identity":{
                        "type": "SystemAssigned"
                    },
                    "properties": {
                        "authCredentials": [
                            {
                                "name": "Credential1",
                                "passwordSecretIdentifier": password_id,  # Optional.
                                "usernameSecretIdentifier": username_id  # Optional.
                            }
                        ],
                        "loginServer": login_server,  # Optional. The credentials are stored for

                    }
                }
    return client.credential_sets.begin_create(resource_group_name=rg,
                                  registry_name=registry_name,
                                  credential_set_name=name,
                                  credential_set_create_parameters=credential_set_create_parameters)

def acr_cred_set_update(cmd,
                   client,
                   registry_name,
                   name,
                   password_id=None,
                   username_id=None):
    if password_id is None and username_id is None:
        raise InvalidArgumentValueError("You must update either the username secret ID, password secret ID, or both.")

    registry, rg = get_registry_by_name(
        cmd.cli_ctx, registry_name, None)

    cred_set = client.credential_sets.get(resource_group_name=rg,
                                  registry_name=registry_name,
                                  credential_set_name=name)


    password_id = password_id if password_id is not None else cred_set['properties']['authCredentials'][0]['passwordSecretIdentifier']
    username_id = username_id if username_id is not None else cred_set['properties']['authCredentials'][0]['usernameSecretIdentifier']

    credential_set_update_parameters = {
                        "name": name,  # Optional. The name of the resource
                        "properties": {
                            "authCredentials": [
                                {
                                    "name": "Credential1",
                                    "passwordSecretIdentifier": password_id,  # Optional.
                                    "usernameSecretIdentifier": username_id  # Optional.
                                }
                            ]
                        }
                    }


    return client.credential_sets.begin_update(resource_group_name=rg,
                                  registry_name=registry_name,
                                  credential_set_name=name,
                                  credential_set_update_parameters=credential_set_update_parameters)
