# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-lines
from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import get_location_type, tags_type


name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME',
                                help='The name of the identity resource.')


def load_arguments(self, _):

    with self.argument_context('identity') as c:
        c.argument('resource_name', arg_type=name_arg_type, id_part='name')

    with self.argument_context('identity create') as c:
        c.argument('location', get_location_type(self.cli_ctx), required=False)
        c.argument('tags', tags_type)

    with self.argument_context('identity federated-credential', min_api='2022-01-31-preview') as c:
        c.argument('federated_credential_name', options_list=('--name', '-n'), help='The name of the federated identity credential resource.')
        c.argument('identity_name', help='The name of the identity resource.')

    for scope in ['identity federated-credential create', 'identity federated-credential update']:
        with self.argument_context(scope) as c:
            c.argument('issuer', help='The openId connect metadata URL of the issuer of the identity provider that Azure AD would use in the token exchange protocol for validating tokens before issuing a token as the user-assigned managed identity.')
            c.argument('subject', help='The sub value in the token sent to Azure AD for getting the user-assigned managed identity token. The value configured in the federated credential and the one in the incoming token must exactly match for Azure AD to issue the access token.')
            c.argument('audiences', nargs='+', help='The aud value in the token sent to Azure for getting the user-assigned managed identity token. The value configured in the federated credential and the one in the incoming token must exactly match for Azure to issue the access token.')
