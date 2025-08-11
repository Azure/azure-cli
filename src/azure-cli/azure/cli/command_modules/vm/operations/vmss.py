# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from azure.cli.core.aaz import has_value
from knack.log import get_logger
from ..aaz.latest.vmss import ListInstances as _VMSSListInstances
from ..aaz.latest.vmss import Deallocate as _VMSSDeallocate

logger = get_logger(__name__)


class VMSSListInstances(_VMSSListInstances):
    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined, has_value

        # Resolve flatten conflict
        # When the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        for value in self.ctx.vars.instance.value:
            if has_value(value.resources):
                for resource in value.resources:
                    if has_value(resource.type):
                        resource.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link


class VMSSDeallocate(_VMSSDeallocate):
    def pre_operations(self):
        args = self.ctx.args

        if has_value(args.instance_ids) and len(args.instance_ids) == 1 and not has_value(args.hibernate):
            self.ctx.args.instance_ids = args.instance_ids[0]
