# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=too-many-locals, too-many-statements, disable=line-too-long
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

    # region NetworkInterfaces
    operations_tmpl = self.get_module_name_by_profile("operations.nic#{}")

    from .operations.nic import NICCreate, NICUpdate
    self.command_table["network nic create"] = NICCreate(loader=self)
    self.command_table["network nic update"] = NICUpdate(loader=self)

    from .operations.nic import NICIPConfigCreate, NICIPConfigUpdate, NICIPConfigNATAdd, NICIPConfigNATRemove
    self.command_table["network nic ip-config create"] = NICIPConfigCreate(loader=self)
    self.command_table["network nic ip-config update"] = NICIPConfigUpdate(loader=self)
    self.command_table["network nic ip-config inbound-nat-rule add"] = NICIPConfigNATAdd(loader=self)
    self.command_table["network nic ip-config inbound-nat-rule remove"] = NICIPConfigNATRemove(loader=self)

    with self.command_group("network nic ip-config address-pool", operations_tmpl=operations_tmpl) as g:
        g.custom_command("add", "add_nic_ip_config_address_pool")
        g.custom_command("remove", "remove_nic_ip_config_address_pool")

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
    from .operations.vnet import VNetCreate, VNetSubnetUpdate
    from .._format import transform_vnet_table_output
    vnet = import_aaz_by_profile("network.vnet")
    self.command_table['network vnet create'] = VNetCreate(loader=self)
    self.command_table['network vnet list'] = vnet.List(loader=self, table_transformer=transform_vnet_table_output)

    self.command_table['network vnet subnet update'] = VNetSubnetUpdate(loader=self)

    # endregion

    # region NetworkRoot
    with self.command_group('network'):
        from .operations.locations import UsagesList
        from .._format import transform_network_usage_table
        self.command_table['network list-usages'] = UsagesList(loader=self,
                                                               table_transformer=transform_network_usage_table)
    # endregion

    # region PublicIPAddresses
    public_ip_show_table_transform = '{Name:name, ResourceGroup:resourceGroup, Location:location, AddressVersion:publicIpAddressVersion, AllocationMethod:publicIpAllocationMethod, IdleTimeoutInMinutes:idleTimeoutInMinutes, ProvisioningState:provisioningState}'

    public_ip = import_aaz_by_profile("network.public_ip")
    operations_tmpl = self.get_module_name_by_profile("operations.public_ip#{}")
    from .._format import transform_public_ip_create_output
    from .._validators import process_public_ip_create_namespace

    with self.command_group('network public-ip', operations_tmpl=operations_tmpl) as g:
        g.custom_command("create", "create_public_ip", transform=transform_public_ip_create_output,
                         validator=process_public_ip_create_namespace)

    self.command_table['network public-ip list'] = public_ip.List(loader=self,
                                                                  table_transformer='[].' + public_ip_show_table_transform)
    self.command_table['network public-ip show'] = public_ip.Show(loader=self,
                                                                  table_transformer=public_ip_show_table_transform)

    # endregion

    # region NetworkSecurityGroups
    from .operations.nsg import NSGCreate, NSGRuleCreate
    from .._format import transform_nsg_rule_table_output
    operations_tmpl = self.get_module_name_by_profile("operations.nsg#{}")
    nsgRule = import_aaz_by_profile("network.nsg.rule")
    self.command_table["network nsg create"] = NSGCreate(loader=self)

    self.command_table["network nsg rule create"] = NSGRuleCreate(loader=self)
    self.command_table["network nsg rule show"] = nsgRule.Show(loader=self, table_transformer=transform_nsg_rule_table_output)
    with self.command_group("network nsg rule", operations_tmpl=operations_tmpl) as g:
        g.custom_command("list", "list_nsg_rules", table_transformer=lambda x: [transform_nsg_rule_table_output(i) for i in x])
    # endregion
