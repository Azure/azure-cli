# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements

from azure.cli.core.commands.parameters import (
    get_three_state_flag,
    get_enum_type
)
from azure.cli.core.commands.validators import validate_file_or_dict
from ..action import (
    AddSoldTo,
    AddEnabledAzurePlans
)

def load_arguments(self, _):

    with self.argument_context('billing') as c:
        c.argument('billing_account_name', options_list=['--name', '-n', '--account-name'], type=str, help=''
                   'The ID that uniquely identifies a billing account.')
