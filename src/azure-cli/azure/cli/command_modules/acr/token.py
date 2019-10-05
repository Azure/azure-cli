# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from ._utils import get_resource_group_name_by_registry_name

SCOPE_MAPS = 'scopeMaps'
TOKENS = 'tokens'


def acr_token_create(cmd,
                     client,
                     registry_name,
                     token_name,
                     scope_map_name,
                     status=None,
                     resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    from ._utils import get_resource_id_by_registry_name

    arm_resource_id = get_resource_id_by_registry_name(cmd.cli_ctx, registry_name)
    scope_map_id = '{}/{}/{}'.format(arm_resource_id, SCOPE_MAPS, scope_map_name)

    Token = cmd.get_models('Token')

    return client.create(
        resource_group_name,
        registry_name,
        token_name,
        Token(
            scope_map_id=scope_map_id,
            status=status
        )
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

    TokenUpdateParameters = cmd.get_models('TokenUpdateParameters')

    scope_map_id = None
    if scope_map_name:
        arm_resource_id = get_resource_id_by_registry_name(cmd.cli_ctx, registry_name)
        scope_map_id = '{}/{}/{}'.format(arm_resource_id, SCOPE_MAPS, scope_map_name)

    return client.update(
        resource_group_name,
        registry_name,
        token_name,
        TokenUpdateParameters(
            scope_map_id=scope_map_id,
            status=status
        )
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
    token_id = '{}/{}/{}'.format(arm_resource_id, TOKENS, token_name)

    # We only want to specify a password if only one was passed.
    name = ("password1" if password1 else "password2") if password1 ^ password2 else None

    if months and not expiry:
        from ._utils import add_months_to_now
        expiry = add_months_to_now(months).isoformat(sep='T')

    GenerateCredentialsParameters = cmd.get_models('GenerateCredentialsParameters')

    return client.generate_credentials(
        resource_group_name,
        registry_name,
        GenerateCredentialsParameters(
            token_id=token_id,
            name=name,
            expiry=expiry
        )
    )


def acr_token_credential_delete(cmd,
                                client,
                                registry_name,
                                token_name,
                                password1=False,
                                password2=False,
                                resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    if not (password1 or password2):
        raise CLIError("Nothing to delete")

    TokenPassword = cmd.get_models('TokenPassword')

    if password1 and password2:
        new_password_payload = []
    elif password1:
        new_password_payload = [
            TokenPassword(
                name="password2"
            )
        ]
    else:
        new_password_payload = [
            TokenPassword(
                name="password1"
            )
        ]

    TokenUpdateParameters = cmd.get_models('TokenUpdateParameters')
    TokenCredentialsProperties = cmd.get_models('TokenCredentialsProperties')

    return client.update(
        resource_group_name,
        registry_name,
        token_name,
        TokenUpdateParameters(
            credentials=TokenCredentialsProperties(
                passwords=new_password_payload
            )
        )
    )
