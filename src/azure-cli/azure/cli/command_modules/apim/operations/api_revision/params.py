# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long


def load_arguments(commands_loader, _):
    with commands_loader.argument_context('apim api revision') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help="The name of the API Management service instance.")
        c.argument('api_id', help='API identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.')
        c.argument('api_revision', help='Describes the Revision of the Api.')
        c.argument('api_revision_description', options_list=['--api-revision-description', '--rev-description'], help='Description of the Api Revision.')
