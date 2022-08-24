# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands.parameters import (get_enum_type, get_three_state_flag)
from azure.mgmt.apimanagement.models import VersioningScheme

VERSIONING_SCHEME = VersioningScheme


def load_arguments(commands_loader, _):
    with commands_loader.argument_context('apim api-version-set') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help="The name of the API Management service instance.")
        c.argument('version_set_id', options_list=['--version-set-id', '--id'], help="A required resource identifier for the related Api Version Set. If a value is not set, it will be auto-generated.")
        c.argument('versioning_scheme', get_enum_type(VERSIONING_SCHEME), options_list=['--versioning-scheme', '-s'], help="Required. determines where the API Version identifer will be located in a HTTP request.")
        c.argument('display_name', help="Required. Name of API Version Set")
        c.argument('description', options_list=['--description', '-d'], help="Description of API Version Set.")
        c.argument('version_query_name', arg_group='Versioning Scheme', help="Name of query parameter. The versioning-scheme must be set to `query`.")
        c.argument('version_header_name', arg_group='Versioning Scheme', help="Name of HTTP header parameter. The versioning-scheme must be set to `header`.")
        c.argument('if_match', help='ETag of the Entity.')
