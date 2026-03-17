# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import register_command, AAZListArg, AAZResourceIdArg
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.command_modules.network.aaz.latest.network.dns._list_references import ListReferences as _DNSListReferences


@register_command("network dns list-references")
class DNSListReferences(_DNSListReferences):
    """ Returns the DNS records specified by the referencing targetResourceIds.

    :example: Returns the DNS records specified by the referencing targetResourceIds.
        az network dns list-references --parameters "/subscriptions/**921/resourceGroups/MyResourceGroup/providers/Microsoft.Network/trafficManagerProfiles/MyTrafficManager"
    """
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.target_resources._registered = False

        args_schema.parameters = AAZListArg(
            options=["--parameters"],
            help="A space-separated list of resource IDs for which referencing dns records need to be queried.",
        )

        parameters = args_schema.parameters
        parameters.Element = AAZResourceIdArg()

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.target_resources = assign_aaz_list_arg(
            args.target_resources,
            args.parameters,
            element_transformer=lambda _, x: {"id": x})
