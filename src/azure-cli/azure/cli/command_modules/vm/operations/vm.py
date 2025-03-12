# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from ..aaz.latest.vm import Show as _VMShow, ListSizes as _VMListSizes

logger = get_logger(__name__)


class VMShow(_VMShow):
    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined, has_value

        # Resolve flatten conflict
        # When the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        if has_value(self.ctx.vars.instance.resources):
            for resource in self.ctx.vars.instance.resources:
                if has_value(resource.type):
                    resource.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class VMListSizes(_VMListSizes):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location._id_part = None

        return args_schema
