# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.command_modules.monitor.aaz.latest.monitor.private_link_scope._create \
    import Create as _PrivateLinkScopeCreate


class PrivateLinkScopeCreate(_PrivateLinkScopeCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location._required = False
        args_schema.location._registered = False
        return args_schema

    def pre_operations(self):
        self.ctx.args.location = "global"
