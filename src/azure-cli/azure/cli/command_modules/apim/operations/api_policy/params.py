# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

def load_arguments(commands_loader, _):
    with commands_loader.argument_context('apim api policy') as c:
        c.argument('api_id', options_list=['--api-id', '-a'], help='API revision identifier. Must be unique in the current API Management service instance.')
        c.argument('xml', options_list=['--xml-value', '-v'], help='The XML document value inline as a non-XML encoded string.')
        c.argument('xml_path', options_list=['--xml-file', '-f'], help='The path to the policy XML document.')
        c.argument('xml_uri', options_list=['--xml-uri', '-u'], help='The URI of the policy XML document from an HTTP endpoint accessible from the API Management service.')
