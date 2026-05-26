# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from ..aaz.latest.vm.host import Show as _VMHostShow

logger = get_logger(__name__)


class VMHostShow(_VMHostShow):
    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        if 'tags' not in result:
            result['tags'] = {}
        return result


def convert_show_result_to_snake_case(result):
    new_result = {}
    if 'location' in result:
        new_result['location'] = result['location']

    if 'sku' in result:
        new_result['sku'] = result['sku']

    if 'tags' in result:
        new_result['tags'] = result['tags']

    if 'autoReplaceOnFailure' in result:
        new_result['auto_replace_on_failure'] = result['autoReplaceOnFailure']

    if 'licenseType' in result:
        new_result['license_type'] = result['licenseType']

    if 'platformFaultDomain' in result:
        new_result['platform_fault_domain'] = result['platformFaultDomain']

    return new_result
