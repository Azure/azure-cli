# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import get_location_type, tags_type

name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME',
                               help='The name of the identity resource.')

def load_arguments(self, _):
    # Base identity parameters
    with self.argument_context('identity') as c:
        c.argument('resource_name', arg_type=name_arg_type, id_part='name')

    with self.argument_context('identity create') as c:
        c.argument('location', get_location_type(self.cli_ctx), required=False)
        c.argument('tags', tags_type)

    # Register federated-credential parameters as part of the identity group
    with self.argument_context('identity federated-credential', is_preview=True) as c:
        c.argument('federated_credential_name', options_list=('--name', '-n'),
                  help='[Preview] The name of the federated identity credential resource. Must start with a letter, number and can contain letters, numbers, underscores, and hyphens. Length must be between 3-120 characters.',
                  type=str)
        c.argument('identity_name',
                  help='[Preview] The name of the user assigned identity.')

    # Register create/update specific parameters
    with self.argument_context('identity federated-credential create', is_preview=True) as c:
        c.argument('issuer',
                  help='[Preview] The URL of the issuer to be trusted.',
                  required=True)
        c.argument('subject',
                  help='[Preview] The identifier of the external identity. Cannot be used with claims-matching-expression-*.')
        c.argument('audiences',
                  nargs='+',
                  help='[Preview] The list of audiences that can appear in the issued token.',
                  required=True)
        c.argument('claims_matching_expression_value',
                  help='[Preview] The wildcard-based expression for matching incoming subject claims. Cannot be used with subject.')
        c.argument('claims_matching_expression_version',
                  type=int,
                  help='[Preview] The version of the claims matching expression language.')

    with self.argument_context('identity federated-credential update', is_preview=True) as c:
        c.argument('issuer',
                  help='[Preview] The URL of the issuer to be trusted.',
                  required=True)
        c.argument('subject',
                  help='[Preview] The identifier of the external identity. Cannot be used with claims-matching-expression-*.')
        c.argument('audiences',
                  nargs='+',
                  help='[Preview] The list of audiences that can appear in the issued token.',
                  required=True)
        c.argument('claims_matching_expression_value',
                  help='[Preview] The wildcard-based expression for matching incoming subject claims. Cannot be used with subject.')
        c.argument('claims_matching_expression_version',
                  type=int,
                  help='[Preview] The version of the claims matching expression language.')
