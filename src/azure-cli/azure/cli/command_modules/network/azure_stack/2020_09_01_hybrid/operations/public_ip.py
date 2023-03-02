# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger
from ._util import import_aaz_by_profile


logger = get_logger(__name__)


_PublicIP = import_aaz_by_profile("network.public_ip")
_PublicIPPrefix = import_aaz_by_profile("network.public_ip.prefix")


def create_public_ip(cmd, resource_group_name, public_ip_address_name, location=None, tags=None,
                     allocation_method=None, dns_name=None,
                     idle_timeout=4, reverse_fqdn=None, version=None, sku=None, zone=None, ip_tags=None,
                     public_ip_prefix=None, ip_address=None):
    public_ip_args = {
        'name': public_ip_address_name,
        "resource_group": resource_group_name,
        'location': location,
        'tags': tags,
        'allocation_method': allocation_method,
        'idle_timeout': idle_timeout,
        'ip_address': ip_address,
        'ip_tags': ip_tags
    }

    if public_ip_prefix:
        from msrestazure.tools import parse_resource_id
        metadata = parse_resource_id(public_ip_prefix)
        resource_group_name = metadata["resource_group"]
        public_ip_prefix_name = metadata["resource_name"]
        public_ip_args["public_ip_prefix"] = public_ip_prefix

        # reuse prefix information
        Show = import_aaz_by_profile("network.public_ip.prefix").Show
        pip_obj = Show(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name, 'name': public_ip_prefix_name})
        version = pip_obj['publicIPAddressVersion']
        sku = pip_obj['sku']['name']
        zone = pip_obj['zones'] if 'zones' in pip_obj else None

    if sku is None:
        logger.warning(
            "Please note that the default public IP used for creation will be changed from Basic to Standard "
            "in the future."
        )

    if not allocation_method:
        if sku and sku.lower() == 'standard':
            public_ip_args['allocation_method'] = 'Static'
        else:
            public_ip_args['allocation_method'] = 'Dynamic'

    public_ip_args['version'] = version
    public_ip_args['zone'] = zone

    if sku:
        public_ip_args['sku'] = sku
    if not sku:
        public_ip_args['sku'] = 'Basic'

    if dns_name or reverse_fqdn:
        public_ip_args['dns_name'] = dns_name
        public_ip_args['reverse_fqdn'] = reverse_fqdn

    return PublicIPCreate(cli_ctx=cmd.cli_ctx)(command_args=public_ip_args)


class PublicIPCreate(_PublicIP.Create):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_prefix._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/publicIPPrefixes/{}",
        )
        return args_schema


class PublicIPUpdate(_PublicIP.Update):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_prefix._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/publicIPPrefixes/{}",
        )
        return args_schema


class PublicIpPrefixCreate(_PublicIPPrefix.Create):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.sku._registered = False
        args_schema.length._required = True

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.sku = {'name': 'Standard'}
