# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network._list_usages import ListUsages as _UsagesList
from azure.cli.command_modules.network._format import transform_network_usage_table


class UsagesList(_UsagesList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_transformer = transform_network_usage_table

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        result = list(result)
        for item in result:
            item['currentValue'] = str(item['currentValue'])
            item['limit'] = str(item['limit'])
            item['localName'] = item['name']['localizedValue']
        return result, next_link
