# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, no-self-use, line-too-long, protected-access, too-few-public-methods
from ._util import import_aaz_by_profile


_NetWork = import_aaz_by_profile("network")


class UsagesList(_NetWork.ListUsages):
    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        result = list(result)
        for item in result:
            item['currentValue'] = str(item['currentValue'])
            item['limit'] = str(item['limit'])
            item['localName'] = item['name']['localizedValue']
        return result, next_link
# endregion
