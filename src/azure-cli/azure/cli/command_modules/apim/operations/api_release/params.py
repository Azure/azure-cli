# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long


def load_arguments(commands_loader, _):
    with commands_loader.argument_context('apim api release') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help="The name of the API Management service instance.")
        c.argument('api_id', help='API identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.')
        c.argument('api_revision', help="API revision number to release and make current.")
        c.argument('release_id', options_list=['--release-id', '--id'], help="Release identifier within an API. Must be unique in the current API Management service instance.")
        c.argument('notes', help="Release Notes.")
        c.argument('if_match', help='ETag of the Entity.')
