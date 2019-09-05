# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from ._utils import get_resource_group_name_by_registry_name


def acr_token_create(cmd,
                     client,
                     registry_name,
                     token_name,
                     scope_map_name,
                     status=None,
                     resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    from ._utils import get_resource_id_by_registry_name

    token_create_parameters = {
        "Properties": {
            "ScopeMapId": None,
            "Credentials": {
            }
        }
    }

    arm_resource_id = get_resource_id_by_registry_name(cmd.cli_ctx, registry_name)
    scope_map_id = arm_resource_id + "/scopeMaps/" + scope_map_name
    token_create_parameters["Properties"]["ScopeMapId"] = scope_map_id

    if status:
        if status not in ["enabled", "disabled"]:
            raise CLIError("Unkown status: {}. Allowed values are 'enabled' or 'disabled'.".format(status))
        token_create_parameters["Properties"]["Status"] = status

    return client.create(
        resource_group_name,
        registry_name,
        token_name,
        token_create_parameters
    )


def acr_token_delete(cmd,
                     client,
                     registry_name,
                     token_name,
                     yes=None,
                     resource_group_name=None):

    if not yes:
        from knack.prompting import prompt_y_n
        confirmation = prompt_y_n("Deleting the token '{}' will invalidate access to anyone using its credentials. "
                                  "Proceed?".format(token_name))

        if not confirmation:
            return None

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return client.delete(resource_group_name, registry_name, token_name)


def acr_token_update(cmd,
                     client,
                     registry_name,
                     token_name,
                     scope_map_name=None,
                     status=None,
                     resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    from ._utils import get_resource_id_by_registry_name

    token_update_parameters = {}

    scope_map_id = None
    if scope_map_name:
        arm_resource_id = get_resource_id_by_registry_name(cmd.cli_ctx, registry_name)
        scope_map_id = arm_resource_id + "/scopeMaps/" + scope_map_name
        token_update_parameters["ScopeMapId"] = scope_map_id

    if status:
        if status not in ["enabled", "disabled"]:
            raise CLIError("Unkown status: {}. Allowed values are 'enabled' or 'disabled'.".format(status))
        token_update_parameters["Status"] = status

    return client.update(
        resource_group_name,
        registry_name,
        token_name,
        token_update_parameters
    )


def acr_token_show(cmd,
                   client,
                   registry_name,
                   token_name,
                   resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.get(
        resource_group_name,
        registry_name,
        token_name
    )


def acr_token_list(cmd,
                   client,
                   registry_name,
                   resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.list(
        resource_group_name,
        registry_name
    )


# Credential functions


def acr_token_credential_generate(cmd,
                                  client,
                                  registry_name,
                                  token_name,
                                  password1=False,
                                  password2=False,
                                  expiry=None,
                                  months=None,
                                  resource_group_name=None):

    from ._utils import get_resource_id_by_registry_name

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    arm_resource_id = get_resource_id_by_registry_name(cmd.cli_ctx, registry_name)
    token_id = arm_resource_id + "/tokens/" + token_name
    generate_credentials_parameters = {"TokenId": token_id}

    if password1 ^ password2:  # We only want to specify a password if only one wass passed.
        generate_credentials_parameters["Name"] = "password1" if password1 else "password2"

    if expiry:
        generate_credentials_parameters["Expiry"] = expiry
    elif months is not None:
        from ._utils import add_months_to_now
        generate_credentials_parameters["Expiry"] = add_months_to_now(months).isoformat(sep='T')

    return client.generate_credentials(
        resource_group_name,
        registry_name,
        generate_credentials_parameters
    )


def acr_token_credential_delete(cmd,
                                client,
                                registry_name,
                                token_name,
                                password1=False,
                                password2=False,
                                resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    if (password1 or password2) is False:
        raise CLIError("Nothing to delete")

    token = acr_token_show(cmd,
                           client,
                           registry_name,
                           token_name,
                           resource_group_name)

    new_passwords = token.credentials.passwords
    if password1:
        new_passwords = [password for password in new_passwords if password.name != "password1"]
    if password2:
        new_passwords = [password for password in new_passwords if password.name != "password2"]

    new_passwords_payload = []
    for password in new_passwords:
        new_passwords_payload.append({
            "Name": password.name
        })

    token_update_parameters = {
        "Credentials": {
            "Passwords": new_passwords_payload
        }
    }

    return client.update(
        resource_group_name,
        registry_name,
        token_name,
        token_update_parameters
    )
