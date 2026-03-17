# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.vnet._update import Update as _VNetUpdate


class VNetUpdate(_VNetUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        # handle detach logic
        args_schema.ddos_protection_plan._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/ddosProtectionPlans/{}",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if args.ipam_pool_prefix_allocations.to_serialized_data():
            args.address_prefixes = []

    def post_instance_update(self, instance):
        if not has_value(instance.properties.ddos_protection_plan.id):
            instance.properties.ddos_protection_plan = None
