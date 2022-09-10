# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import get_three_state_flag


def load_arguments(commands_loader, _):
    api_id = CLIArgumentType(arg_group='API',
                             help='API identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.')
    schema_id = CLIArgumentType(arg_group='Schema',
                                help='Schema identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.')

    # common arguments
    with commands_loader.argument_context('apim api schema') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help='The name of the API Management service instance.')
        c.argument('api_id', options_list=['--api-id', '-a'], arg_type=api_id, required=True)
        c.argument('schema_id', options_list=['--schema-id', '-s'], arg_type=schema_id, required=True)

    with commands_loader.argument_context('apim api schema create') as c:
        c.argument('schema_name', help='The name of the schema resource.')
        c.argument('schema_path', options_list=['--schema-file', '-f'], arg_group='Schema', help='File path specified to import schema of the API.')
        c.argument('schema_content', options_list=['--schema-content', '-c'], help='Json escaped string defining the document representing the Schema')
        c.argument('schema_type', options_list=['--schema-type', '-t'], arg_group='Schema',
                   help='Schema content type. Must be a valid media type used in a Content-Type header as defined in the RFC 2616. Media type of the schema document (e.g. application/json, application/xml).',
                   required=True)
        c.argument('if_match', help='ETag of the Entity.')

    with commands_loader.argument_context('apim api schema delete') as c:
        c.argument('if_match', help='ETag of the Entity.')

    with commands_loader.argument_context('apim api schema list') as c:
        c.argument('filter_display_name', arg_group='Schema', help='Filter of APIs by displayName.')
        c.argument('skip', type=int, help='Number of records to skip.')
        c.argument('top', type=int, help='Number of records to return.')

    with commands_loader.argument_context('apim api schema show') as c:
        c.argument('include_schema_value', arg_type=get_three_state_flag(), options_list=['--include-schema-value'], help="Specify to indicate whether the schema value should be returned. True if flag present.")
