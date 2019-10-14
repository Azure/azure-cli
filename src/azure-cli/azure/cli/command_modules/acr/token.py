# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from ._utils import get_resource_group_name_by_registry_name, validate_premium_registry

SCOPE_MAPS = 'scopeMaps'
TOKENS = 'tokens'


def acr_token_create(cmd,
                     client,
                     registry_name,
                     token_name,
                     scope_map_name,
                     status=None,
                     resource_group_name=None):

    validate_premium_registry(cmd, registry_name, resource_group_name)

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
                                  days=None,
                                  resource_group_name=None):

    from ._utils import get_resource_id_by_registry_name

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    arm_resource_id = get_resource_id_by_registry_name(cmd.cli_ctx, registry_name)
    token_id = '{}/{}/{}'.format(arm_resource_id, TOKENS, token_name)

    # We only want to specify a password if only one was passed.
    name = ("password1" if password1 else "password2") if password1 ^ password2 else None
    expiry = None
    if days:
        from ._utils import add_days_to_now
        expiry = add_days_to_now(days)

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

    if not (password1 or password2):
        raise CLIError('No credentials to delete.')

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    token = client.get(
        resource_group_name,
        registry_name,
        token_name
    )

    # retrieve the set of existing Token password names. Eg: {'password1', 'password2'}
    password_names = set(map(lambda password: password.name, token.credentials.passwords))

    if password1 and 'password1' not in password_names:
        raise CLIError('Unable to perform operation. Password1 credential doesn\'t exist.')
    if password2 and 'password2' not in password_names:
        raise CLIError('Unable to perform operation. Password2 credential doesn\'t exist.')

    # remove the items which are supposed to be deleted
    if password1:
        password_names.remove('password1')
    if password2:
        password_names.remove('password2')

    TokenPassword = cmd.get_models('TokenPassword')
    new_password_payload = list(map(lambda name: TokenPassword(name=name), password_names))

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
