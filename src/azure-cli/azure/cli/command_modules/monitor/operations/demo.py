# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from ..aaz.latest.monitor.log_analytics.cluster import Create as _ClusterCreate



class ClusterCreate(_ClusterCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.assigned_identity = AAZListArg(options=['--assigned-identity'], help="Argument help message...")
        args_schema.assigned_identity.Element = AAZStrArg()

        return args_schema

    def _cli_arguments_loader(self):
        args = super()._cli_arguments_loader()
        args = [(name, arg) for (name, arg) in args if name not in ("identity_type", "user_assigned")]
        return args

    def pre_operations(self):
        from azure.cli.core.aaz import has_value
        args = self.ctx.args
        if has_value(args.assigned_identity):
            systen_assigned = False
            user_assigned = False
            for identity in args.assigned_identity:
                identity = str(identity)
                if identity.lower() == "[system]":
                    systen_assigned = True
                else:
                    user_assigned = True
                    args.user_assigned[identity] = {}
            if systen_assigned and user_assigned:
                args.identity_type = "SystemAssigned,UserAssigned"
            elif systen_assigned:
                args.identity_type = "SystemAssigned"
            elif user_assigned:
                args.identity_type = "UserAssigned"
            else:
                args.identity_type = "None"
