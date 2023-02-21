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

    from .operations.load_balancer import LBOutboundRuleCreate, LBOutboundRuleUpdate
    self.command_table["network lb outbound-rule create"] = LBOutboundRuleCreate(loader=self)
    self.command_table["network lb outbound-rule update"] = LBOutboundRuleUpdate(loader=self)

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
    from .operations.vpn_connection import VpnConnectionUpdate, VpnConnectionDeviceConfigScriptShow
    self.command_table['network vpn-connection update'] = VpnConnectionUpdate(loader=self)
    self.command_table['network vpn-connection show-device-config-script'] = VpnConnectionDeviceConfigScriptShow(
        loader=self)

    from .operations.vpn_connection import VpnConnSharedKeyUpdate
    self.command_table['network vpn-connection shared-key update'] = VpnConnSharedKeyUpdate(loader=self)

    from .operations.vpn_connection import VpnConnIpsecPolicyAdd
    self.command_table['network vpn-connection ipsec-policy add'] = VpnConnIpsecPolicyAdd(loader=self)

    operations_tmpl = self.get_module_name_by_profile("operations.vpn_connection#{}")
    with self.command_group('network vpn-connection', operations_tmpl=operations_tmpl) as g:
        g.command('list', 'list_vpn_connections')
        g.command('ipsec-policy clear', 'clear_vpn_conn_ipsec_policies', supports_no_wait=True)

    # endregion
