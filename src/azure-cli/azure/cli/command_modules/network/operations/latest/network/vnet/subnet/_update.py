# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.command_modules.network.aaz.latest.network.vnet.subnet._update import Update as _VNetSubnetUpdate
from azure.cli.command_modules.network.custom import _handle_plural_or_singular, subnet_disable_ple_msg, subnet_disable_pls_msg

from knack.log import get_logger

logger = get_logger(__name__)


class VNetSubnetUpdate(_VNetSubnetUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.delegations = AAZListArg(
            options=["--delegations"],
            help="Space-separated list of services to whom the subnet should be delegated, e.g., Microsoft.Sql/servers.",
            nullable=True,
        )
        args_schema.delegations.Element = AAZStrArg(
            nullable=True,
        )
        # add endpoint/policy arguments
        args_schema.service_endpoints = AAZListArg(
            options=["--service-endpoints"],
            help="Space-separated list of services allowed private access to this subnet. "
                 "Values from: az network vnet list-endpoint-services.",
            nullable=True,
        )
        args_schema.service_endpoints.Element = AAZStrArg(
            nullable=True,
        )
        args_schema.service_endpoint_policy = AAZListArg(
            options=["--service-endpoint-policy"],
            help="Space-separated list of names or IDs of service endpoint policies to apply.",
            nullable=True,
        )
        args_schema.service_endpoint_policy.Element = AAZResourceIdArg(
            nullable=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/serviceEndpointPolicies/{}",
            ),
        )
        # add ple/pls arguments
        args_schema.disable_private_endpoint_network_policies = AAZStrArg(
            options=["--disable-private-endpoint-network-policies"],
            help="Disable private endpoint network policies on the subnet. Please note that it will be replaced by `--private-endpoint-network-policies` soon.",
            nullable=True,
            enum={
                "true": "Disabled", "t": "Disabled", "yes": "Disabled", "y": "Disabled", "1": "Disabled",
                "false": "Enabled", "f": "Enabled", "no": "Enabled", "n": "Enabled", "0": "Enabled",
            },
            blank="Disabled",
        )
        args_schema.disable_private_link_service_network_policies = AAZStrArg(
            options=["--disable-private-link-service-network-policies"],
            help="Disable private link service network policies on the subnet. Please note that it will be replaced by `--private-link-service-network-policies` soon.",
            nullable=True,
            enum={
                "true": "Disabled", "t": "Disabled", "yes": "Disabled", "y": "Disabled", "1": "Disabled",
                "false": "Enabled", "f": "Enabled", "no": "Enabled", "n": "Enabled", "0": "Enabled",
            },
            blank="Disabled",
        )
        # filter arguments
        args_schema.address_prefix._registered = False
        args_schema.delegated_services._registered = False
        args_schema.policies._registered = False
        # handle detach logic
        args_schema.nat_gateway._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/natGateways/{}",
        )
        args_schema.network_security_group._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/networkSecurityGroups/{}",
        )
        args_schema.route_table._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/routeTables/{}",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        _handle_plural_or_singular(args, "address_prefixes", "address_prefix")

        def delegation_trans(index, service_name):
            service_name = str(service_name)
            # covert name to service name
            if "/" not in service_name and len(service_name.split(".")) == 3:
                _, service, resource_type = service_name.split(".")
                service_name = f"Microsoft.{service}/{resource_type}"
            return {
                "name": str(index),
                "service_name": service_name,
            }

        if has_value(args.endpoints) and has_value(args.service_endpoints):
            raise ArgumentUsageError("usage error: `--endpoints` and `--service-endpoints` cannot be used together, we prefer to use `endpoints` instead")
        args.delegated_services = assign_aaz_list_arg(
            args.delegated_services,
            args.delegations,
            element_transformer=delegation_trans
        )
        args.endpoints = assign_aaz_list_arg(
            args.endpoints,
            args.service_endpoints,
            element_transformer=lambda _, service_name: {"service": service_name}
        )
        args.policies = assign_aaz_list_arg(
            args.policies,
            args.service_endpoint_policy,
            element_transformer=lambda _, policy_id: {"id": policy_id}
        )
        # use string instead of bool
        if has_value(args.disable_private_endpoint_network_policies):
            logger.warning(subnet_disable_ple_msg)
            args.private_endpoint_network_policies = args.disable_private_endpoint_network_policies
        if has_value(args.disable_private_link_service_network_policies):
            logger.warning(subnet_disable_pls_msg)
            args.private_link_service_network_policies = args.disable_private_link_service_network_policies

        if args.ipam_pool_prefix_allocations.to_serialized_data():
            args.address_prefixes = []

    def post_instance_update(self, instance):
        if not has_value(instance.properties.network_security_group.id):
            instance.properties.network_security_group = None
        if not has_value(instance.properties.route_table.id):
            instance.properties.route_table = None
        if not has_value(instance.properties.nat_gateway.id):
            instance.properties.nat_gateway = None
