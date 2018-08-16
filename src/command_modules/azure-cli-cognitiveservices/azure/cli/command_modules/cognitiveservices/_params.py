# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from knack.arguments import CLIArgumentType
from knack.log import get_logger

from azure.cli.core.commands.parameters import (
    tags_type,
    resource_group_name_type,
    get_resource_name_completion_list)
from azure.cli.core.util import (shell_safe_json_parse, CLIError)

from azure.cli.core.commands.validators import validate_tag

logger = get_logger(__name__)
name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')


def extract_key_values_pairs(api_properties):
    api_properties_dict = {}
    for item in api_properties:
        api_properties_dict.update(validate_tag(item))
    return api_properties_dict


def validate_api_properties(ns):
    """ Extracts JSON format or 'a=b c=d' format as api properties """
    api_properties = ns.api_properties

    if api_properties is None:
        return

    if len(api_properties) > 1:
        ns.api_properties = extract_key_values_pairs(api_properties)
    else:
        string = api_properties[0]
        try:
            ns.api_properties = shell_safe_json_parse(string)
            return
        except CLIError:
            result = extract_key_values_pairs([string])
            if _is_suspected_json(string):
                logger.warning('Api properties looks like a JSON format but not valid, interpreted as key=value pairs:'
                               ' %s', str(result))
            ns.api_properties = result
            return


def _is_suspected_json(string):
    """ If the string looks like a JSON """
    if string.startswith('{') or string.startswith('\'{') or string.startswith('\"{'):
        return True
    if string.startswith('[') or string.startswith('\'[') or string.startswith('\"['):
        return True
    if re.match(r"^['\"\s]*{.+}|\[.+\]['\"\s]*$", string):
        return True

    return False


api_properties_type = CLIArgumentType(
    validator=validate_api_properties,
    help="Api properties in JSON format or a=b c=d format. Some cognitive services (i.e. QnA Maker) "
         "require extra api properties to create the account.",
    nargs='*'
)


def load_arguments(self, _):
    with self.argument_context('cognitiveservices') as c:
        c.argument('account_name', arg_type=name_arg_type, help='cognitive service account name',
                   completer=get_resource_name_completion_list('Microsoft.CognitiveServices/accounts'))
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('sku_name', options_list=['--sku'], help='the Sku of cognitive services account')
        c.argument('kind', help='the API name of cognitive services account')
        c.argument('tags', tags_type)
        c.argument('key_name', required=True, help='Key name to generate', choices=['key1', 'key2'])
        c.argument('api_properties', api_properties_type)

    with self.argument_context('cognitiveservices account create') as c:
        c.argument('yes', action='store_true', help='Do not prompt for terms confirmation')
