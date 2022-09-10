# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands.parameters import (tags_type, get_three_state_flag)


def load_arguments(commands_loader, _):
    with commands_loader.argument_context('apim named-value') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help='The name of the API Management service instance.')
        c.argument('named_value_id', options_list=['--id'], help='Identifier of the NamedValue.')
        c.argument('display_name', options_list=['--display-name', '-d'], help='Required. Unique name of NamedValue. It may contain only letters, digits, period, dash, and underscore characters.')
        c.argument('value', options_list=['--value', '-v'], help='Required. Value of the NamedValue. Can contain policy expressions. It may not be empty or consist only of whitespace. This property will not be filled on GET operations! Use /listSecrets POST request to get the value.')
        c.argument('secret', arg_type=get_three_state_flag(), help='Determines whether the value is a secret. Default value is false.')
        c.argument('tags', tags_type)
        c.argument('if_match', help='ETag of the integration runtime entity. Should only be specified for update, for '
                   'which it should match existing entity or can be * for unconditional update.')

    with commands_loader.argument_context('apim named-value show') as c:
        c.argument('secret', arg_type=get_three_state_flag(), help='Whether the value is a secret and should display the value. Default value is false.')
