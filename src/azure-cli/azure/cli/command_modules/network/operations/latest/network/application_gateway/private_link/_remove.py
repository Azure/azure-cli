# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.azclierror import ValidationError
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.private_link._remove import Remove as _AGPrivateLinkRemove


class AGPrivateLinkRemove(_AGPrivateLinkRemove):
    def pre_instance_delete(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        for plc in instance.properties.private_link_configurations:
            if plc.name == args.name:
                to_be_removed = plc
                break
        else:
            err_msg = "Private link doesn't exist."
            raise ValidationError(err_msg)

        for fic in instance.properties.frontend_ip_configurations:
            if has_value(fic.properties.private_link_configuration) \
                    and fic.properties.private_link_configuration.id == to_be_removed.id:
                fic.properties.private_link_configuration = None
