# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long


def load_arguments(commands_loader, _):
    with commands_loader.argument_context('apim product api') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help="The name of the API Management service instance", id_part=None)
        c.argument('product_id', options_list=['--product-id', '-p'], help="Product identifier. Must be unique in the current API Management service instance.")
        c.argument('api_id', help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.')
