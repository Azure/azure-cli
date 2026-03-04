# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.command_modules.network.aaz.latest.network.vnet_gateway.nat_rule._add import Add as _VnetGatewayNatRuleAdd


class VnetGatewayNatRuleAdd(_VnetGatewayNatRuleAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.external_mappings = AAZListArg(
            options=["--external-mappings"],
            help="The private IP address external mapping for NAT.",
            required=True
        )
        args_schema.external_mappings.Element = AAZStrArg()
        args_schema.internal_mappings = AAZListArg(
            options=["--internal-mappings"],
            help="The private IP address internal mapping for NAT.",
            required=True
        )
        args_schema.internal_mappings.Element = AAZStrArg()

        args_schema.external_mappings_ip._registered = False
        args_schema.internal_mappings_ip._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.external_mappings):
            args.external_mappings_ip = assign_aaz_list_arg(
                args.external_mappings_ip,
                args.external_mappings,
                element_transformer=lambda _, external_mapping: {"address_space": external_mapping}
            )

        if has_value(args.internal_mappings):
            args.internal_mappings_ip = assign_aaz_list_arg(
                args.internal_mappings_ip,
                args.internal_mappings,
                element_transformer=lambda _, internal_mapping: {"address_space": internal_mapping}
            )

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        if has_value(self.ctx.vars.instance.properties.nat_rules):
            nat_rules = self.ctx.vars.instance.properties.natRules.to_serialized_data()
            for nat_rule in nat_rules:
                if 'type' in nat_rule['properties']:
                    nat_rule['properties']['type'] = AAZUndefined
            self.ctx.vars.instance.properties.nat_rules = nat_rules
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
