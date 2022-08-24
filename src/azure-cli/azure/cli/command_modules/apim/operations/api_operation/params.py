# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.command_modules.apim.operations.api_operation.actions import TemplateParameter


def load_arguments(commands_loader, _):
    with commands_loader.argument_context('apim api operation') as c:
        c.argument('operation_id', options_list=['--operation-id', '--id'], help='Operation identifier within an API. Must be unique in the current API Management service instance.')
        c.argument('description', help="Description of the operation. May include HTML formatting tags.")
        c.argument('template_parameters', options_list=['--template-parameters', '--params', '-p'], action=TemplateParameter, nargs='+', help="Collection of URL template parameters.")
        c.argument('method', help="Required. A Valid HTTP Operation Method. Typical Http Methods like GET, PUT, POST but not limited by only them.")
        c.argument('display_name', help="Required. Operation Name.")
        c.argument('if_match', help='ETag of the Entity.')
        c.argument('url_template', help='Relative URL template identifying the target resource for this operation. May include parameters.')
