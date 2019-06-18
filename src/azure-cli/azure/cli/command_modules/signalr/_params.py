# pylint: disable=line-too-long
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    get_location_type,
    get_resource_name_completion_list,
    tags_type
)

from knack.log import get_logger

from ._constants import (
    SIGNALR_RESOURCE_TYPE,
    SIGNALR_KEY_TYPE
)


logger = get_logger(__name__)


def load_arguments(self, _):
    with self.argument_context('signalr') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location',
                   arg_type=get_location_type(self.cli_ctx),
                   validator=get_default_location_from_resource_group)
        c.argument('signalr_name', options_list=['--name', '-n'],
                   completer=get_resource_name_completion_list(SIGNALR_RESOURCE_TYPE),
                   help='Name of signalr service.')
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('signalr create') as c:
        c.argument('sku', help='The sku name of the signalr service. E.g. Standard_S1')
        c.argument('unit_count', help='The number of signalr service unit count', type=int)

    with self.argument_context('signalr key renew') as c:
        c.argument('key_type', help='The name of access key to regenerate', choices=SIGNALR_KEY_TYPE)
