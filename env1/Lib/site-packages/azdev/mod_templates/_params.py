# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType


def load_arguments(self, _):

    from azure.cli.core.commands.parameters import tags_type
    from azure.cli.core.commands.validators import get_default_location_from_resource_group

    {{ sdk_property }}_type = CLIArgumentType(options_list='--{{ sdk_property.replace("_", "-") }}-name', help='Name of the {{ display_name }}.', id_part='name')

    with self.argument_context('{{ name }}') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('{{ sdk_property }}', {{ sdk_property }}_type, options_list=['--name', '-n'])

    with self.argument_context('{{ name }} list') as c:
        c.argument('{{ sdk_property }}', {{ sdk_property }}_type, id_part=None)

