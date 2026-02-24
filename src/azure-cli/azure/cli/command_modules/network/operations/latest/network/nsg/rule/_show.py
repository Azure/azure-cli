# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.nsg.rule._show import Show as _NSGRuleShow
from azure.cli.command_modules.network._format import transform_nsg_rule_table_output


class NSGRuleShow(_NSGRuleShow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_transformer = transform_nsg_rule_table_output
