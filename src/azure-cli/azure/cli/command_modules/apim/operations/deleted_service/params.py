# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands.parameters import get_location_type


def load_arguments(commands_loader, _):
    with commands_loader.argument_context('apim deleted-service') as c:
        c.argument('location', arg_type=get_location_type(commands_loader.cli_ctx))
        c.argument('service_name', options_list=['--service-name', '-n'], help="The name of the soft deleted API Management service instance.")
