# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.azclierror import ValidationError
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.private_link.ip_config._add import Add as _AGPrivateLinkIPConfigAdd


class AGPrivateLinkIPConfigAdd(_AGPrivateLinkIPConfigAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.private_ip_allocation_method._registered = False
        args_schema.subnet._registered = False
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        for plc in instance.properties.private_link_configurations:
            if plc.name == args.private_link:
                target_private_link = plc
                break
        else:
            err_msg = "Private link doesn't exist."
            raise ValidationError(err_msg)

        args.private_ip_allocation_method = "Static" if has_value(args.ip_address) else "Dynamic"
        subnet_id = target_private_link.properties.ip_configurations[0].properties.subnet.id
        args.subnet.id = subnet_id
