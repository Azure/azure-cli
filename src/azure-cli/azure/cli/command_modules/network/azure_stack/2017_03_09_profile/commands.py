# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):
    from .operations import import_aaz_by_profile

    # region LoadBalancers
    from .operations.load_balancer import LBFrontendIPCreate, LBFrontendIPUpdate
    self.command_table["network lb frontend-ip create"] = LBFrontendIPCreate(loader=self)
    self.command_table["network lb frontend-ip update"] = LBFrontendIPUpdate(loader=self)

    from .operations.load_balancer import LBInboundNatRuleCreate, LBInboundNatRuleUpdate
    self.command_table["network lb inbound-nat-rule create"] = LBInboundNatRuleCreate(loader=self)
    self.command_table["network lb inbound-nat-rule update"] = LBInboundNatRuleUpdate(loader=self)

    from .operations.load_balancer import LBInboundNatPoolCreate, LBInboundNatPoolUpdate
    self.command_table["network lb inbound-nat-pool create"] = LBInboundNatPoolCreate(loader=self)
    self.command_table["network lb inbound-nat-pool update"] = LBInboundNatPoolUpdate(loader=self)

    from .operations.load_balancer import LBRuleCreate, LBRuleUpdate
    self.command_table["network lb rule create"] = LBRuleCreate(loader=self)
    self.command_table["network lb rule update"] = LBRuleUpdate(loader=self)

    from .operations.load_balancer import LBProbeCreate, LBProbeUpdate
    self.command_table["network lb probe create"] = LBProbeCreate(loader=self)
    self.command_table["network lb probe update"] = LBProbeUpdate(loader=self)

    # endregion

    # region LocalNetworkGateways
    local_gateway = import_aaz_by_profile("network.local_gateway")

    from .._format import transform_local_gateway_table_output
    self.command_table['network local-gateway list'] = local_gateway.List(
        loader=self, table_transformer=transform_local_gateway_table_output)

    # endregion

    # region VirtualNetworkGatewayConnections
    from .operations.vpn_connection import VpnConnSharedKeyUpdate
    self.command_table['network vpn-connection shared-key update'] = VpnConnSharedKeyUpdate(loader=self)

    # endregion

    # region VirtualNetworkGateways
    from .operations.vnet_gateway import VnetGatewayCreate, VnetGatewayUpdate
    self.command_table['network vnet-gateway create'] = VnetGatewayCreate(loader=self)
    self.command_table['network vnet-gateway update'] = VnetGatewayUpdate(loader=self)

    from .operations.vnet_gateway import VnetGatewayRevokedCertCreate
    self.command_table['network vnet-gateway revoked-cert create'] = VnetGatewayRevokedCertCreate(loader=self)

    from .operations.vnet_gateway import VnetGatewayRootCertCreate
    self.command_table['network vnet-gateway root-cert create'] = VnetGatewayRootCertCreate(loader=self)

    # region VirtualNetwork
    from .operations.vnet import VNetCreate, VNetUpdate, VNetSubnetUpdate
    from .._format import transform_vnet_table_output
    vnet = import_aaz_by_profile("network.vnet")
    self.command_table['network vnet create'] = VNetCreate(loader=self)
    self.command_table['network vnet update'] = VNetUpdate(loader=self)
    self.command_table['network vnet list'] = vnet.List(loader=self, table_transformer=transform_vnet_table_output)

    self.command_table['network vnet subnet update'] = VNetSubnetUpdate(loader=self)

    # endregion

    # region PublicIPAddresses
    public_ip_show_table_transform = '{Name:name, ResourceGroup:resourceGroup, Location:location, $zone$Address:ipAddress, AddressVersion:publicIpAddressVersion, AllocationMethod:publicIpAllocationMethod, IdleTimeoutInMinutes:idleTimeoutInMinutes, ProvisioningState:provisioningState}'
    public_ip_show_table_transform = public_ip_show_table_transform.replace('$zone$', 'Zones: (!zones && \' \') || join(` `, zones), ' if self.supported_api_version(min_api='2017-06-01') else ' ')

    public_ip = import_aaz_by_profile("network.public_ip")
    operations_tmpl = self.get_module_name_by_profile("operations.public_ip#{}")
    from .._format import transform_public_ip_create_output
    from .._validators import get_default_location_from_resource_group

    with self.command_group('network public-ip', operations_tmpl=operations_tmpl) as g:
        g.custom_command("create", "create_public_ip", transform=transform_public_ip_create_output, validator=get_default_location_from_resource_group)

    self.command_table['network public-ip list'] = public_ip.List(loader=self, table_transformer='[].' + public_ip_show_table_transform)
    self.command_table['network public-ip show'] = public_ip.Show(loader=self, table_transformer=public_ip_show_table_transform)

    # endregion
