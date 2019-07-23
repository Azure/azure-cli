# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import (get_enum_type,
                                                get_location_type,
                                                resource_group_name_type,
                                                get_three_state_flag)
from ._validators import (validate_capacity)

SKU_TYPES = ['Developer', 'Basic', 'Standard', 'Premium', 'Consumption']

def load_arguments(self, _):

    from azure.cli.core.commands.parameters import tags_type
    from azure.cli.core.commands.validators import get_default_location_from_resource_group

    with self.argument_context('apim') as c:
        c.argument('tags', tags_type)
        #c.argument('service_name', options_list=['--name', '-n'], help="The name of the api management service instance.")
        c.argument('name', options_list=['--name', '-n'], help="The name of the api management service instance", id_part='name')
        c.argument('location', validator=get_default_location_from_resource_group)

    with self.argument_context('apim create') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('publisher_name', help='The name of your organization for use in the developer portal and e-mail notifications.')
        c.argument('publisher_email', help='The e-mail address to receive all system notifications sent from API Management')
        c.argument('sku', arg_type=get_enum_type(SKU_TYPES), help='The sku of the api management instance')
        c.argument('capacity', type=int, validator=validate_capacity, help='The number of units of the api management instance')
        c.argument('enable_client_certificate', arg_type=get_three_state_flag(), help='meant to be used for Consumption SKU Service. This enforces a client certificate to be presented on each request to the gateway. This also enables the ability to authenticate the certificate in the policy on the gateway')

    for subgroup in ['api', 'product']:
        with self.argument_context('apim {}'.format(subgroup)) as c:
            c.argument('service_name', options_list=['--service-name', '-sn'])
