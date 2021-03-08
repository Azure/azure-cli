# Azure CLI Module Creation Report

## EXTENSION
|CLI Extension|Command Groups|
|---------|------------|
|az network|[groups](#CommandGroups)

## GROUPS
### <a name="CommandGroups">Command groups in `az network` extension </a>
|CLI Command Group|Group Swagger name|Commands|
|---------|------------|--------|
|az network application-gateway|ApplicationGateways|[commands](#CommandsInApplicationGateways)|
|az network application-gateway-private-endpoint-connection|ApplicationGatewayPrivateEndpointConnections|[commands](#CommandsInApplicationGatewayPrivateEndpointConnections)|
|az network application-security-group|ApplicationSecurityGroups|[commands](#CommandsInApplicationSecurityGroups)|
|az network web-category|WebCategories|[commands](#CommandsInWebCategories)|
|az network||[commands](#CommandsIn)|
|az network network-interface|NetworkInterfaces|[commands](#CommandsInNetworkInterfaces)|
|az network public-ip-address|PublicIPAddresses|[commands](#CommandsInPublicIPAddresses)|
|az network custom-ip-prefix|CustomIPPrefixes|[commands](#CommandsInCustomIPPrefixes)|
|az network express-route-circuit-connection|ExpressRouteCircuitConnections|[commands](#CommandsInExpressRouteCircuitConnections)|
|az network express-route-circuit|ExpressRouteCircuits|[commands](#CommandsInExpressRouteCircuits)|
|az network express-route-cross-connection-peering|ExpressRouteCrossConnectionPeerings|[commands](#CommandsInExpressRouteCrossConnectionPeerings)|
|az network load-balancer-frontend-ip-configuration|LoadBalancerFrontendIPConfigurations|[commands](#CommandsInLoadBalancerFrontendIPConfigurations)|
|az network inbound-nat-rule|InboundNatRules|[commands](#CommandsInInboundNatRules)|
|az network load-balancer-network-interface|LoadBalancerNetworkInterfaces|[commands](#CommandsInLoadBalancerNetworkInterfaces)|
|az network network-interface-ip-configuration|NetworkInterfaceIPConfigurations|[commands](#CommandsInNetworkInterfaceIPConfigurations)|
|az network network-interface-load-balancer|NetworkInterfaceLoadBalancers|[commands](#CommandsInNetworkInterfaceLoadBalancers)|
|az network network-interface-tap-configuration|NetworkInterfaceTapConfigurations|[commands](#CommandsInNetworkInterfaceTapConfigurations)|
|az network default-security-rule|DefaultSecurityRules|[commands](#CommandsInDefaultSecurityRules)|
|az network network-watcher|NetworkWatchers|[commands](#CommandsInNetworkWatchers)|
|az network private-link-service|PrivateLinkServices|[commands](#CommandsInPrivateLinkServices)|
|az network virtual-network|VirtualNetworks|[commands](#CommandsInVirtualNetworks)|
|az network subnet|Subnets|[commands](#CommandsInSubnets)|
|az network resource-navigation-link|ResourceNavigationLinks|[commands](#CommandsInResourceNavigationLinks)|
|az network service-association-link|ServiceAssociationLinks|[commands](#CommandsInServiceAssociationLinks)|
|az network virtual-network-gateway|VirtualNetworkGateways|[commands](#CommandsInVirtualNetworkGateways)|
|az network virtual-network-gateway-connection|VirtualNetworkGatewayConnections|[commands](#CommandsInVirtualNetworkGatewayConnections)|
|az network virtual-network-tap|VirtualNetworkTaps|[commands](#CommandsInVirtualNetworkTaps)|
|az network vpn-site-link|VpnSiteLinks|[commands](#CommandsInVpnSiteLinks)|
|az network vpn-gateway|VpnGateways|[commands](#CommandsInVpnGateways)|
|az network vpn-connection|VpnConnections|[commands](#CommandsInVpnConnections)|
|az network vpn-site-link-connection|VpnSiteLinkConnections|[commands](#CommandsInVpnSiteLinkConnections)|
|az network nat-rule|NatRules|[commands](#CommandsInNatRules)|
|az network p2-s-vpn-gateway|P2sVpnGateways|[commands](#CommandsInP2sVpnGateways)|
|az network vpn-server-configuration-associated-with-virtual-wan|VpnServerConfigurationsAssociatedWithVirtualWan|[commands](#CommandsInVpnServerConfigurationsAssociatedWithVirtualWan)|
|az network virtual-hub-bgp-connection|VirtualHubBgpConnection|[commands](#CommandsInVirtualHubBgpConnection)|
|az network virtual-hub-bgp-connection|VirtualHubBgpConnections|[commands](#CommandsInVirtualHubBgpConnections)|
|az network virtual-hub-ip-configuration|VirtualHubIpConfiguration|[commands](#CommandsInVirtualHubIpConfiguration)|

## COMMANDS
### <a name="CommandsIn">Commands in `az network` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network generatevirtualwanvpnserverconfigurationvpnprofile](#generatevirtualwanvpnserverconfigurationvpnprofile)|generatevirtualwanvpnserverconfigurationvpnprofile|[Parameters](#Parametersgeneratevirtualwanvpnserverconfigurationvpnprofile)|[Example](#Examplesgeneratevirtualwanvpnserverconfigurationvpnprofile)|
|[az network get-active-session](#GetActiveSessions)|GetActiveSessions|[Parameters](#ParametersGetActiveSessions)|[Example](#ExamplesGetActiveSessions)|
|[az network supported-security-provider](#SupportedSecurityProviders)|SupportedSecurityProviders|[Parameters](#ParametersSupportedSecurityProviders)|[Example](#ExamplesSupportedSecurityProviders)|

### <a name="CommandsInApplicationGateways">Commands in `az network application-gateway` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network application-gateway backend-health-on-demand](#ApplicationGatewaysBackendHealthOnDemand)|BackendHealthOnDemand|[Parameters](#ParametersApplicationGatewaysBackendHealthOnDemand)|[Example](#ExamplesApplicationGatewaysBackendHealthOnDemand)|

### <a name="CommandsInApplicationGatewayPrivateEndpointConnections">Commands in `az network application-gateway-private-endpoint-connection` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network application-gateway-private-endpoint-connection show](#ApplicationGatewayPrivateEndpointConnectionsGet)|Get|[Parameters](#ParametersApplicationGatewayPrivateEndpointConnectionsGet)|[Example](#ExamplesApplicationGatewayPrivateEndpointConnectionsGet)|

### <a name="CommandsInApplicationSecurityGroups">Commands in `az network application-security-group` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network application-security-group list](#ApplicationSecurityGroupsList)|List|[Parameters](#ParametersApplicationSecurityGroupsList)|[Example](#ExamplesApplicationSecurityGroupsList)|

### <a name="CommandsInCustomIPPrefixes">Commands in `az network custom-ip-prefix` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network custom-ip-prefix list](#CustomIPPrefixesList)|List|[Parameters](#ParametersCustomIPPrefixesList)|[Example](#ExamplesCustomIPPrefixesList)|
|[az network custom-ip-prefix show](#CustomIPPrefixesGet)|Get|[Parameters](#ParametersCustomIPPrefixesGet)|[Example](#ExamplesCustomIPPrefixesGet)|
|[az network custom-ip-prefix list-all](#CustomIPPrefixesListAll)|ListAll|[Parameters](#ParametersCustomIPPrefixesListAll)|[Example](#ExamplesCustomIPPrefixesListAll)|

### <a name="CommandsInDefaultSecurityRules">Commands in `az network default-security-rule` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network default-security-rule list](#DefaultSecurityRulesList)|List|[Parameters](#ParametersDefaultSecurityRulesList)|[Example](#ExamplesDefaultSecurityRulesList)|
|[az network default-security-rule show](#DefaultSecurityRulesGet)|Get|[Parameters](#ParametersDefaultSecurityRulesGet)|[Example](#ExamplesDefaultSecurityRulesGet)|

### <a name="CommandsInExpressRouteCircuits">Commands in `az network express-route-circuit` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network express-route-circuit list-route-table-summary](#ExpressRouteCircuitsListRoutesTableSummary)|ListRoutesTableSummary|[Parameters](#ParametersExpressRouteCircuitsListRoutesTableSummary)|[Example](#ExamplesExpressRouteCircuitsListRoutesTableSummary)|
|[az network express-route-circuit show-peering-stat](#ExpressRouteCircuitsGetPeeringStats)|GetPeeringStats|[Parameters](#ParametersExpressRouteCircuitsGetPeeringStats)|[Example](#ExamplesExpressRouteCircuitsGetPeeringStats)|

### <a name="CommandsInExpressRouteCircuitConnections">Commands in `az network express-route-circuit-connection` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network express-route-circuit-connection list](#ExpressRouteCircuitConnectionsList)|List|[Parameters](#ParametersExpressRouteCircuitConnectionsList)|[Example](#ExamplesExpressRouteCircuitConnectionsList)|

### <a name="CommandsInExpressRouteCrossConnectionPeerings">Commands in `az network express-route-cross-connection-peering` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network express-route-cross-connection-peering show](#ExpressRouteCrossConnectionPeeringsGet)|Get|[Parameters](#ParametersExpressRouteCrossConnectionPeeringsGet)|[Example](#ExamplesExpressRouteCrossConnectionPeeringsGet)|
|[az network express-route-cross-connection-peering create](#ExpressRouteCrossConnectionPeeringsCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersExpressRouteCrossConnectionPeeringsCreateOrUpdate#Create)|[Example](#ExamplesExpressRouteCrossConnectionPeeringsCreateOrUpdate#Create)|
|[az network express-route-cross-connection-peering update](#ExpressRouteCrossConnectionPeeringsCreateOrUpdate#Update)|CreateOrUpdate#Update|[Parameters](#ParametersExpressRouteCrossConnectionPeeringsCreateOrUpdate#Update)|Not Found|
|[az network express-route-cross-connection-peering delete](#ExpressRouteCrossConnectionPeeringsDelete)|Delete|[Parameters](#ParametersExpressRouteCrossConnectionPeeringsDelete)|[Example](#ExamplesExpressRouteCrossConnectionPeeringsDelete)|

### <a name="CommandsInInboundNatRules">Commands in `az network inbound-nat-rule` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network inbound-nat-rule show](#InboundNatRulesGet)|Get|[Parameters](#ParametersInboundNatRulesGet)|[Example](#ExamplesInboundNatRulesGet)|
|[az network inbound-nat-rule create](#InboundNatRulesCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersInboundNatRulesCreateOrUpdate#Create)|[Example](#ExamplesInboundNatRulesCreateOrUpdate#Create)|
|[az network inbound-nat-rule update](#InboundNatRulesCreateOrUpdate#Update)|CreateOrUpdate#Update|[Parameters](#ParametersInboundNatRulesCreateOrUpdate#Update)|Not Found|
|[az network inbound-nat-rule delete](#InboundNatRulesDelete)|Delete|[Parameters](#ParametersInboundNatRulesDelete)|[Example](#ExamplesInboundNatRulesDelete)|

### <a name="CommandsInLoadBalancerFrontendIPConfigurations">Commands in `az network load-balancer-frontend-ip-configuration` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network load-balancer-frontend-ip-configuration list](#LoadBalancerFrontendIPConfigurationsList)|List|[Parameters](#ParametersLoadBalancerFrontendIPConfigurationsList)|[Example](#ExamplesLoadBalancerFrontendIPConfigurationsList)|

### <a name="CommandsInLoadBalancerNetworkInterfaces">Commands in `az network load-balancer-network-interface` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network load-balancer-network-interface list](#LoadBalancerNetworkInterfacesList)|List|[Parameters](#ParametersLoadBalancerNetworkInterfacesList)|[Example](#ExamplesLoadBalancerNetworkInterfacesList)|

### <a name="CommandsInNatRules">Commands in `az network nat-rule` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network nat-rule list](#NatRulesListByVpnGateway)|ListByVpnGateway|[Parameters](#ParametersNatRulesListByVpnGateway)|[Example](#ExamplesNatRulesListByVpnGateway)|

### <a name="CommandsInNetworkInterfaces">Commands in `az network network-interface` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network network-interface show-virtual-machine-scale-set-ip-configuration](#NetworkInterfacesGetVirtualMachineScaleSetIpConfiguration)|GetVirtualMachineScaleSetIpConfiguration|[Parameters](#ParametersNetworkInterfacesGetVirtualMachineScaleSetIpConfiguration)|[Example](#ExamplesNetworkInterfacesGetVirtualMachineScaleSetIpConfiguration)|

### <a name="CommandsInNetworkInterfaceIPConfigurations">Commands in `az network network-interface-ip-configuration` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network network-interface-ip-configuration list](#NetworkInterfaceIPConfigurationsList)|List|[Parameters](#ParametersNetworkInterfaceIPConfigurationsList)|[Example](#ExamplesNetworkInterfaceIPConfigurationsList)|
|[az network network-interface-ip-configuration show](#NetworkInterfaceIPConfigurationsGet)|Get|[Parameters](#ParametersNetworkInterfaceIPConfigurationsGet)|[Example](#ExamplesNetworkInterfaceIPConfigurationsGet)|

### <a name="CommandsInNetworkInterfaceLoadBalancers">Commands in `az network network-interface-load-balancer` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network network-interface-load-balancer list](#NetworkInterfaceLoadBalancersList)|List|[Parameters](#ParametersNetworkInterfaceLoadBalancersList)|[Example](#ExamplesNetworkInterfaceLoadBalancersList)|

### <a name="CommandsInNetworkInterfaceTapConfigurations">Commands in `az network network-interface-tap-configuration` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network network-interface-tap-configuration list](#NetworkInterfaceTapConfigurationsList)|List|[Parameters](#ParametersNetworkInterfaceTapConfigurationsList)|[Example](#ExamplesNetworkInterfaceTapConfigurationsList)|
|[az network network-interface-tap-configuration delete](#NetworkInterfaceTapConfigurationsDelete)|Delete|[Parameters](#ParametersNetworkInterfaceTapConfigurationsDelete)|[Example](#ExamplesNetworkInterfaceTapConfigurationsDelete)|

### <a name="CommandsInNetworkWatchers">Commands in `az network network-watcher` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network network-watcher get-azure-reachability-report](#NetworkWatchersGetAzureReachabilityReport)|GetAzureReachabilityReport|[Parameters](#ParametersNetworkWatchersGetAzureReachabilityReport)|[Example](#ExamplesNetworkWatchersGetAzureReachabilityReport)|
|[az network network-watcher list-available-provider](#NetworkWatchersListAvailableProviders)|ListAvailableProviders|[Parameters](#ParametersNetworkWatchersListAvailableProviders)|[Example](#ExamplesNetworkWatchersListAvailableProviders)|

### <a name="CommandsInP2sVpnGateways">Commands in `az network p2-s-vpn-gateway` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network p2-s-vpn-gateway disconnect-p2-s-vpn-connection](#P2sVpnGatewaysDisconnectP2sVpnConnections)|DisconnectP2sVpnConnections|[Parameters](#ParametersP2sVpnGatewaysDisconnectP2sVpnConnections)|[Example](#ExamplesP2sVpnGatewaysDisconnectP2sVpnConnections)|
|[az network p2-s-vpn-gateway get-p2-s-vpn-connection-health](#P2sVpnGatewaysGetP2sVpnConnectionHealth)|GetP2sVpnConnectionHealth|[Parameters](#ParametersP2sVpnGatewaysGetP2sVpnConnectionHealth)|[Example](#ExamplesP2sVpnGatewaysGetP2sVpnConnectionHealth)|
|[az network p2-s-vpn-gateway get-p2-s-vpn-connection-health-detailed](#P2sVpnGatewaysGetP2sVpnConnectionHealthDetailed)|GetP2sVpnConnectionHealthDetailed|[Parameters](#ParametersP2sVpnGatewaysGetP2sVpnConnectionHealthDetailed)|[Example](#ExamplesP2sVpnGatewaysGetP2sVpnConnectionHealthDetailed)|
|[az network p2-s-vpn-gateway reset](#P2sVpnGatewaysReset)|Reset|[Parameters](#ParametersP2sVpnGatewaysReset)|[Example](#ExamplesP2sVpnGatewaysReset)|

### <a name="CommandsInPrivateLinkServices">Commands in `az network private-link-service` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network private-link-service list-private-endpoint-connection](#PrivateLinkServicesListPrivateEndpointConnections)|ListPrivateEndpointConnections|[Parameters](#ParametersPrivateLinkServicesListPrivateEndpointConnections)|[Example](#ExamplesPrivateLinkServicesListPrivateEndpointConnections)|
|[az network private-link-service show-private-endpoint-connection](#PrivateLinkServicesGetPrivateEndpointConnection)|GetPrivateEndpointConnection|[Parameters](#ParametersPrivateLinkServicesGetPrivateEndpointConnection)|[Example](#ExamplesPrivateLinkServicesGetPrivateEndpointConnection)|

### <a name="CommandsInPublicIPAddresses">Commands in `az network public-ip-address` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network public-ip-address list-virtual-machine-scale-set-vm-public-ip-address](#PublicIPAddressesListVirtualMachineScaleSetVMPublicIPAddresses)|ListVirtualMachineScaleSetVMPublicIPAddresses|[Parameters](#ParametersPublicIPAddressesListVirtualMachineScaleSetVMPublicIPAddresses)|[Example](#ExamplesPublicIPAddressesListVirtualMachineScaleSetVMPublicIPAddresses)|
|[az network public-ip-address show-virtual-machine-scale-set-public-ip-address](#PublicIPAddressesGetVirtualMachineScaleSetPublicIPAddress)|GetVirtualMachineScaleSetPublicIPAddress|[Parameters](#ParametersPublicIPAddressesGetVirtualMachineScaleSetPublicIPAddress)|[Example](#ExamplesPublicIPAddressesGetVirtualMachineScaleSetPublicIPAddress)|

### <a name="CommandsInResourceNavigationLinks">Commands in `az network resource-navigation-link` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network resource-navigation-link list](#ResourceNavigationLinksList)|List|[Parameters](#ParametersResourceNavigationLinksList)|[Example](#ExamplesResourceNavigationLinksList)|

### <a name="CommandsInServiceAssociationLinks">Commands in `az network service-association-link` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network service-association-link list](#ServiceAssociationLinksList)|List|[Parameters](#ParametersServiceAssociationLinksList)|[Example](#ExamplesServiceAssociationLinksList)|

### <a name="CommandsInSubnets">Commands in `az network subnet` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network subnet prepare-network-policy](#SubnetsPrepareNetworkPolicies)|PrepareNetworkPolicies|[Parameters](#ParametersSubnetsPrepareNetworkPolicies)|[Example](#ExamplesSubnetsPrepareNetworkPolicies)|
|[az network subnet unprepare-network-policy](#SubnetsUnprepareNetworkPolicies)|UnprepareNetworkPolicies|[Parameters](#ParametersSubnetsUnprepareNetworkPolicies)|[Example](#ExamplesSubnetsUnprepareNetworkPolicies)|

### <a name="CommandsInVirtualHubBgpConnection">Commands in `az network virtual-hub-bgp-connection` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network virtual-hub-bgp-connection delete](#VirtualHubBgpConnectionDelete)|Delete|[Parameters](#ParametersVirtualHubBgpConnectionDelete)|[Example](#ExamplesVirtualHubBgpConnectionDelete)|

### <a name="CommandsInVirtualHubBgpConnections">Commands in `az network virtual-hub-bgp-connection` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network virtual-hub-bgp-connection list-advertised-route](#VirtualHubBgpConnectionsListAdvertisedRoutes)|ListAdvertisedRoutes|[Parameters](#ParametersVirtualHubBgpConnectionsListAdvertisedRoutes)|[Example](#ExamplesVirtualHubBgpConnectionsListAdvertisedRoutes)|
|[az network virtual-hub-bgp-connection list-learned-route](#VirtualHubBgpConnectionsListLearnedRoutes)|ListLearnedRoutes|[Parameters](#ParametersVirtualHubBgpConnectionsListLearnedRoutes)|[Example](#ExamplesVirtualHubBgpConnectionsListLearnedRoutes)|

### <a name="CommandsInVirtualHubIpConfiguration">Commands in `az network virtual-hub-ip-configuration` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network virtual-hub-ip-configuration list](#VirtualHubIpConfigurationList)|List|[Parameters](#ParametersVirtualHubIpConfigurationList)|[Example](#ExamplesVirtualHubIpConfigurationList)|

### <a name="CommandsInVirtualNetworks">Commands in `az network virtual-network` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network virtual-network list-usage](#VirtualNetworksListUsage)|ListUsage|[Parameters](#ParametersVirtualNetworksListUsage)|[Example](#ExamplesVirtualNetworksListUsage)|

### <a name="CommandsInVirtualNetworkGateways">Commands in `az network virtual-network-gateway` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network virtual-network-gateway disconnect-virtual-network-gateway-vpn-connection](#VirtualNetworkGatewaysDisconnectVirtualNetworkGatewayVpnConnections)|DisconnectVirtualNetworkGatewayVpnConnections|[Parameters](#ParametersVirtualNetworkGatewaysDisconnectVirtualNetworkGatewayVpnConnections)|[Example](#ExamplesVirtualNetworkGatewaysDisconnectVirtualNetworkGatewayVpnConnections)|
|[az network virtual-network-gateway get-vpnclient-connection-health](#VirtualNetworkGatewaysGetVpnclientConnectionHealth)|GetVpnclientConnectionHealth|[Parameters](#ParametersVirtualNetworkGatewaysGetVpnclientConnectionHealth)|[Example](#ExamplesVirtualNetworkGatewaysGetVpnclientConnectionHealth)|
|[az network virtual-network-gateway get-vpnclient-ipsec-parameter](#VirtualNetworkGatewaysGetVpnclientIpsecParameters)|GetVpnclientIpsecParameters|[Parameters](#ParametersVirtualNetworkGatewaysGetVpnclientIpsecParameters)|[Example](#ExamplesVirtualNetworkGatewaysGetVpnclientIpsecParameters)|
|[az network virtual-network-gateway list-connection](#VirtualNetworkGatewaysListConnections)|ListConnections|[Parameters](#ParametersVirtualNetworkGatewaysListConnections)|[Example](#ExamplesVirtualNetworkGatewaysListConnections)|
|[az network virtual-network-gateway set-vpnclient-ipsec-parameter](#VirtualNetworkGatewaysSetVpnclientIpsecParameters)|SetVpnclientIpsecParameters|[Parameters](#ParametersVirtualNetworkGatewaysSetVpnclientIpsecParameters)|[Example](#ExamplesVirtualNetworkGatewaysSetVpnclientIpsecParameters)|
|[az network virtual-network-gateway start-packet-capture](#VirtualNetworkGatewaysStartPacketCapture)|StartPacketCapture|[Parameters](#ParametersVirtualNetworkGatewaysStartPacketCapture)|[Example](#ExamplesVirtualNetworkGatewaysStartPacketCapture)|
|[az network virtual-network-gateway stop-packet-capture](#VirtualNetworkGatewaysStopPacketCapture)|StopPacketCapture|[Parameters](#ParametersVirtualNetworkGatewaysStopPacketCapture)|[Example](#ExamplesVirtualNetworkGatewaysStopPacketCapture)|
|[az network virtual-network-gateway supported-vpn-device](#VirtualNetworkGatewaysSupportedVpnDevices)|SupportedVpnDevices|[Parameters](#ParametersVirtualNetworkGatewaysSupportedVpnDevices)|[Example](#ExamplesVirtualNetworkGatewaysSupportedVpnDevices)|
|[az network virtual-network-gateway vpn-device-configuration-script](#VirtualNetworkGatewaysVpnDeviceConfigurationScript)|VpnDeviceConfigurationScript|[Parameters](#ParametersVirtualNetworkGatewaysVpnDeviceConfigurationScript)|[Example](#ExamplesVirtualNetworkGatewaysVpnDeviceConfigurationScript)|

### <a name="CommandsInVirtualNetworkGatewayConnections">Commands in `az network virtual-network-gateway-connection` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network virtual-network-gateway-connection get-ike-sas](#VirtualNetworkGatewayConnectionsGetIkeSas)|GetIkeSas|[Parameters](#ParametersVirtualNetworkGatewayConnectionsGetIkeSas)|[Example](#ExamplesVirtualNetworkGatewayConnectionsGetIkeSas)|
|[az network virtual-network-gateway-connection start-packet-capture](#VirtualNetworkGatewayConnectionsStartPacketCapture)|StartPacketCapture|[Parameters](#ParametersVirtualNetworkGatewayConnectionsStartPacketCapture)|[Example](#ExamplesVirtualNetworkGatewayConnectionsStartPacketCapture)|
|[az network virtual-network-gateway-connection stop-packet-capture](#VirtualNetworkGatewayConnectionsStopPacketCapture)|StopPacketCapture|[Parameters](#ParametersVirtualNetworkGatewayConnectionsStopPacketCapture)|[Example](#ExamplesVirtualNetworkGatewayConnectionsStopPacketCapture)|

### <a name="CommandsInVirtualNetworkTaps">Commands in `az network virtual-network-tap` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network virtual-network-tap list](#VirtualNetworkTapsListByResourceGroup)|ListByResourceGroup|[Parameters](#ParametersVirtualNetworkTapsListByResourceGroup)|[Example](#ExamplesVirtualNetworkTapsListByResourceGroup)|
|[az network virtual-network-tap show](#VirtualNetworkTapsGet)|Get|[Parameters](#ParametersVirtualNetworkTapsGet)|[Example](#ExamplesVirtualNetworkTapsGet)|
|[az network virtual-network-tap delete](#VirtualNetworkTapsDelete)|Delete|[Parameters](#ParametersVirtualNetworkTapsDelete)|[Example](#ExamplesVirtualNetworkTapsDelete)|

### <a name="CommandsInVpnConnections">Commands in `az network vpn-connection` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network vpn-connection start-packet-capture](#VpnConnectionsStartPacketCapture)|StartPacketCapture|[Parameters](#ParametersVpnConnectionsStartPacketCapture)|[Example](#ExamplesVpnConnectionsStartPacketCapture)|
|[az network vpn-connection stop-packet-capture](#VpnConnectionsStopPacketCapture)|StopPacketCapture|[Parameters](#ParametersVpnConnectionsStopPacketCapture)|[Example](#ExamplesVpnConnectionsStopPacketCapture)|

### <a name="CommandsInVpnGateways">Commands in `az network vpn-gateway` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network vpn-gateway reset](#VpnGatewaysReset)|Reset|[Parameters](#ParametersVpnGatewaysReset)|[Example](#ExamplesVpnGatewaysReset)|
|[az network vpn-gateway start-packet-capture](#VpnGatewaysStartPacketCapture)|StartPacketCapture|[Parameters](#ParametersVpnGatewaysStartPacketCapture)|[Example](#ExamplesVpnGatewaysStartPacketCapture)|
|[az network vpn-gateway stop-packet-capture](#VpnGatewaysStopPacketCapture)|StopPacketCapture|[Parameters](#ParametersVpnGatewaysStopPacketCapture)|[Example](#ExamplesVpnGatewaysStopPacketCapture)|

### <a name="CommandsInVpnServerConfigurationsAssociatedWithVirtualWan">Commands in `az network vpn-server-configuration-associated-with-virtual-wan` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network vpn-server-configuration-associated-with-virtual-wan list](#VpnServerConfigurationsAssociatedWithVirtualWanList)|List|[Parameters](#ParametersVpnServerConfigurationsAssociatedWithVirtualWanList)|[Example](#ExamplesVpnServerConfigurationsAssociatedWithVirtualWanList)|

### <a name="CommandsInVpnSiteLinks">Commands in `az network vpn-site-link` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network vpn-site-link list](#VpnSiteLinksListByVpnSite)|ListByVpnSite|[Parameters](#ParametersVpnSiteLinksListByVpnSite)|[Example](#ExamplesVpnSiteLinksListByVpnSite)|
|[az network vpn-site-link show](#VpnSiteLinksGet)|Get|[Parameters](#ParametersVpnSiteLinksGet)|[Example](#ExamplesVpnSiteLinksGet)|

### <a name="CommandsInVpnSiteLinkConnections">Commands in `az network vpn-site-link-connection` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network vpn-site-link-connection show](#VpnSiteLinkConnectionsGet)|Get|[Parameters](#ParametersVpnSiteLinkConnectionsGet)|[Example](#ExamplesVpnSiteLinkConnectionsGet)|

### <a name="CommandsInWebCategories">Commands in `az network web-category` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network web-category list](#WebCategoriesListBySubscription)|ListBySubscription|[Parameters](#ParametersWebCategoriesListBySubscription)|[Example](#ExamplesWebCategoriesListBySubscription)|


## COMMAND DETAILS

### group `az network`
#### <a name="generatevirtualwanvpnserverconfigurationvpnprofile">Command `az network generatevirtualwanvpnserverconfigurationvpnprofile`</a>

##### <a name="Examplesgeneratevirtualwanvpnserverconfigurationvpnprofile">Example</a>
```
az network generatevirtualwanvpnserverconfigurationvpnprofile --resource-group "rg1" --virtual-wan-name "wan1" \
--authentication-method "EAPTLS" --vpn-server-configuration-resource-id "/subscriptions/subid/resourceGroups/rg1/provid\
ers/Microsoft.Network/vpnServerConfigurations/vpnconfig1"
```
##### <a name="Parametersgeneratevirtualwanvpnserverconfigurationvpnprofile">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|
|**--virtual-wan-name**|string|The name of the VirtualWAN whose associated VpnServerConfigurations is needed.|virtual_wan_name|virtualWANName|
|**--vpn-server-configuration-resource-id**|string|VpnServerConfiguration partial resource uri with which VirtualWan is associated to.|vpn_server_configuration_resource_id|vpnServerConfigurationResourceId|
|**--authentication-method**|choice|VPN client authentication method.|authentication_method|authenticationMethod|

#### <a name="GetActiveSessions">Command `az network get-active-session`</a>

##### <a name="ExamplesGetActiveSessions">Example</a>
```
az network get-active-session --bastion-host-name "bastionhosttenant" --resource-group "rg1"
```
##### <a name="ParametersGetActiveSessions">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--bastion-host-name**|string|The name of the Bastion Host.|bastion_host_name|bastionHostName|

#### <a name="SupportedSecurityProviders">Command `az network supported-security-provider`</a>

##### <a name="ExamplesSupportedSecurityProviders">Example</a>
```
az network supported-security-provider --resource-group "rg1" --virtual-wan-name "wan1"
```
##### <a name="ParametersSupportedSecurityProviders">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|
|**--virtual-wan-name**|string|The name of the VirtualWAN for which supported security providers are needed.|virtual_wan_name|virtualWANName|

### group `az network application-gateway`
#### <a name="ApplicationGatewaysBackendHealthOnDemand">Command `az network application-gateway backend-health-on-demand`</a>

##### <a name="ExamplesApplicationGatewaysBackendHealthOnDemand">Example</a>
```
az network application-gateway backend-health-on-demand --name "appgw" --path "/" --sub-resource-id \
"/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/applicationGateways/appgw/backendaddressPools/MFAn\
alyticsPool" --id "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/applicationGateways/appgw/backen\
dHttpSettingsCollection/MFPoolSettings" --pick-host-name-from-backend-http-settings true --timeout 30 --protocol \
"Http" --resource-group "rg1"
```
##### <a name="ParametersApplicationGatewaysBackendHealthOnDemand">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--application-gateway-name**|string|The name of the application gateway.|application_gateway_name|applicationGatewayName|
|**--expand**|string|Expands BackendAddressPool and BackendHttpSettings referenced in backend health.|expand|$expand|
|**--protocol**|choice|The protocol used for the probe.|protocol|protocol|
|**--host**|string|Host name to send the probe to.|host|host|
|**--path**|string|Relative path of probe. Valid path starts from '/'. Probe is sent to <Protocol>://<host>:<port><path>.|path|path|
|**--timeout**|integer|The probe timeout in seconds. Probe marked as failed if valid response is not received with this timeout period. Acceptable values are from 1 second to 86400 seconds.|timeout|timeout|
|**--pick-host-name-from-backend-http-settings**|boolean|Whether the host header should be picked from the backend http settings. Default value is false.|pick_host_name_from_backend_http_settings|pickHostNameFromBackendHttpSettings|
|**--match**|object|Criterion for classifying a healthy probe response.|match|match|
|**--id**|string|Resource ID.|id|id|
|**--sub-resource-id**|string|Resource ID.|sub_resource_id|id|

### group `az network application-gateway-private-endpoint-connection`
#### <a name="ApplicationGatewayPrivateEndpointConnectionsGet">Command `az network application-gateway-private-endpoint-connection show`</a>

##### <a name="ExamplesApplicationGatewayPrivateEndpointConnectionsGet">Example</a>
```
az network application-gateway-private-endpoint-connection show --application-gateway-name "appgw" --connection-name \
"connection1" --resource-group "rg1"
```
##### <a name="ParametersApplicationGatewayPrivateEndpointConnectionsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--application-gateway-name**|string|The name of the application gateway.|application_gateway_name|applicationGatewayName|
|**--connection-name**|string|The name of the application gateway private endpoint connection.|connection_name|connectionName|

### group `az network application-security-group`
#### <a name="ApplicationSecurityGroupsList">Command `az network application-security-group list`</a>

##### <a name="ExamplesApplicationSecurityGroupsList">Example</a>
```
az network application-security-group list --resource-group "rg1"
```
##### <a name="ParametersApplicationSecurityGroupsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|

### group `az network custom-ip-prefix`
#### <a name="CustomIPPrefixesList">Command `az network custom-ip-prefix list`</a>

##### <a name="ExamplesCustomIPPrefixesList">Example</a>
```
az network custom-ip-prefix list --resource-group "rg1"
```
##### <a name="ParametersCustomIPPrefixesList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|

#### <a name="CustomIPPrefixesGet">Command `az network custom-ip-prefix show`</a>

##### <a name="ExamplesCustomIPPrefixesGet">Example</a>
```
az network custom-ip-prefix show --name "test-customipprefix" --resource-group "rg1"
```
##### <a name="ParametersCustomIPPrefixesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--custom-ip-prefix-name**|string|The name of the custom IP prefix.|custom_ip_prefix_name|customIpPrefixName|
|**--expand**|string|Expands referenced resources.|expand|$expand|

#### <a name="CustomIPPrefixesListAll">Command `az network custom-ip-prefix list-all`</a>

##### <a name="ExamplesCustomIPPrefixesListAll">Example</a>
```
az network custom-ip-prefix list-all
```
##### <a name="ParametersCustomIPPrefixesListAll">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
### group `az network default-security-rule`
#### <a name="DefaultSecurityRulesList">Command `az network default-security-rule list`</a>

##### <a name="ExamplesDefaultSecurityRulesList">Example</a>
```
az network default-security-rule list --nsg-name "nsg1" --resource-group "testrg"
```
##### <a name="ParametersDefaultSecurityRulesList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--network-security-group-name**|string|The name of the network security group.|network_security_group_name|networkSecurityGroupName|

#### <a name="DefaultSecurityRulesGet">Command `az network default-security-rule show`</a>

##### <a name="ExamplesDefaultSecurityRulesGet">Example</a>
```
az network default-security-rule show --name "AllowVnetInBound" --nsg-name "nsg1" --resource-group "testrg"
```
##### <a name="ParametersDefaultSecurityRulesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--network-security-group-name**|string|The name of the network security group.|network_security_group_name|networkSecurityGroupName|
|**--default-security-rule-name**|string|The name of the default security rule.|default_security_rule_name|defaultSecurityRuleName|

### group `az network express-route-circuit`
#### <a name="ExpressRouteCircuitsListRoutesTableSummary">Command `az network express-route-circuit list-route-table-summary`</a>

##### <a name="ExamplesExpressRouteCircuitsListRoutesTableSummary">Example</a>
```
az network express-route-circuit list-route-table-summary --circuit-name "circuitName" --device-path "devicePath" \
--peering-name "peeringName" --resource-group "rg1"
```
##### <a name="ParametersExpressRouteCircuitsListRoutesTableSummary">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--circuit-name**|string|The name of the express route circuit.|circuit_name|circuitName|
|**--peering-name**|string|The name of the peering.|peering_name|peeringName|
|**--device-path**|string|The path of the device.|device_path|devicePath|

#### <a name="ExpressRouteCircuitsGetPeeringStats">Command `az network express-route-circuit show-peering-stat`</a>

##### <a name="ExamplesExpressRouteCircuitsGetPeeringStats">Example</a>
```
az network express-route-circuit show-peering-stat --circuit-name "circuitName" --peering-name "peeringName" \
--resource-group "rg1"
```
##### <a name="ParametersExpressRouteCircuitsGetPeeringStats">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--circuit-name**|string|The name of the express route circuit.|circuit_name|circuitName|
|**--peering-name**|string|The name of the peering.|peering_name|peeringName|

### group `az network express-route-circuit-connection`
#### <a name="ExpressRouteCircuitConnectionsList">Command `az network express-route-circuit-connection list`</a>

##### <a name="ExamplesExpressRouteCircuitConnectionsList">Example</a>
```
az network express-route-circuit-connection list --circuit-name "ExpressRouteARMCircuitA" --peering-name \
"AzurePrivatePeering" --resource-group "rg1"
```
##### <a name="ParametersExpressRouteCircuitConnectionsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--circuit-name**|string|The name of the circuit.|circuit_name|circuitName|
|**--peering-name**|string|The name of the peering.|peering_name|peeringName|

### group `az network express-route-cross-connection-peering`
#### <a name="ExpressRouteCrossConnectionPeeringsGet">Command `az network express-route-cross-connection-peering show`</a>

##### <a name="ExamplesExpressRouteCrossConnectionPeeringsGet">Example</a>
```
az network express-route-cross-connection-peering show --cross-connection-name "<circuitServiceKey>" --peering-name \
"AzurePrivatePeering" --resource-group "CrossConnection-SiliconValley"
```
##### <a name="ParametersExpressRouteCrossConnectionPeeringsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--cross-connection-name**|string|The name of the ExpressRouteCrossConnection.|cross_connection_name|crossConnectionName|
|**--peering-name**|string|The name of the peering.|peering_name|peeringName|

#### <a name="ExpressRouteCrossConnectionPeeringsCreateOrUpdate#Create">Command `az network express-route-cross-connection-peering create`</a>

##### <a name="ExamplesExpressRouteCrossConnectionPeeringsCreateOrUpdate#Create">Example</a>
```
az network express-route-cross-connection-peering create --cross-connection-name "<circuitServiceKey>" --peering-name \
"AzurePrivatePeering" --ipv6-express-route-circuit-peering-config-primary-peer-address-prefix-primary-peer-address-pref\
ix "3FFE:FFFF:0:CD30::/126" --ipv6-express-route-circuit-peering-config-secondary-peer-address-prefix-secondary-peer-ad\
dress-prefix "3FFE:FFFF:0:CD30::4/126" --peer-asn 200 --primary-peer-address-prefix "192.168.16.252/30" \
--secondary-peer-address-prefix "192.168.18.252/30" --vlan-id 200 --resource-group "CrossConnection-SiliconValley"
```
##### <a name="ParametersExpressRouteCrossConnectionPeeringsCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--cross-connection-name**|string|The name of the ExpressRouteCrossConnection.|cross_connection_name|crossConnectionName|
|**--peering-name**|string|The name of the peering.|peering_name|peeringName|
|**--id**|string|Resource ID.|id|id|
|**--name**|string|The name of the resource that is unique within a resource group. This name can be used to access the resource.|name|name|
|**--peering-type**|choice|The peering type.|peering_type|peeringType|
|**--state**|choice|The peering state.|state|state|
|**--peer-asn**|integer|The peer ASN.|peer_asn|peerASN|
|**--primary-peer-address-prefix**|string|The primary address prefix.|primary_peer_address_prefix|primaryPeerAddressPrefix|
|**--secondary-peer-address-prefix**|string|The secondary address prefix.|secondary_peer_address_prefix|secondaryPeerAddressPrefix|
|**--shared-key**|string|The shared key.|shared_key|sharedKey|
|**--vlan-id**|integer|The VLAN ID.|vlan_id|vlanId|
|**--microsoft-peering-config**|object|The Microsoft peering configuration.|microsoft_peering_config|microsoftPeeringConfig|
|**--gateway-manager-etag**|string|The GatewayManager Etag.|gateway_manager_etag|gatewayManagerEtag|
|**--ipv6-express-route-circuit-peering-config-primary-peer-address-prefix-primary-peer-address-prefix**|string|The primary address prefix.|ipv6_express_route_circuit_peering_config_primary_peer_address_prefix_primary_peer_address_prefix|primaryPeerAddressPrefix|
|**--ipv6-express-route-circuit-peering-config-secondary-peer-address-prefix-secondary-peer-address-prefix**|string|The secondary address prefix.|ipv6_express_route_circuit_peering_config_secondary_peer_address_prefix_secondary_peer_address_prefix|secondaryPeerAddressPrefix|
|**--express-route-circuit-peering-config-microsoft-peering-config**|object|The Microsoft peering configuration.|express_route_circuit_peering_config_microsoft_peering_config|microsoftPeeringConfig|
|**--express-route-circuit-peering-state**|choice|The state of peering.|express_route_circuit_peering_state|state|
|**--sub-resource-id**|string|Resource ID.|sub_resource_id|id|

#### <a name="ExpressRouteCrossConnectionPeeringsCreateOrUpdate#Update">Command `az network express-route-cross-connection-peering update`</a>

##### <a name="ParametersExpressRouteCrossConnectionPeeringsCreateOrUpdate#Update">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--cross-connection-name**|string|The name of the ExpressRouteCrossConnection.|cross_connection_name|crossConnectionName|
|**--peering-name**|string|The name of the peering.|peering_name|peeringName|
|**--id**|string|Resource ID.|id|id|
|**--name**|string|The name of the resource that is unique within a resource group. This name can be used to access the resource.|name|name|
|**--peering-type**|choice|The peering type.|peering_type|peeringType|
|**--state**|choice|The peering state.|state|state|
|**--peer-asn**|integer|The peer ASN.|peer_asn|peerASN|
|**--primary-peer-address-prefix**|string|The primary address prefix.|primary_peer_address_prefix|primaryPeerAddressPrefix|
|**--secondary-peer-address-prefix**|string|The secondary address prefix.|secondary_peer_address_prefix|secondaryPeerAddressPrefix|
|**--shared-key**|string|The shared key.|shared_key|sharedKey|
|**--vlan-id**|integer|The VLAN ID.|vlan_id|vlanId|
|**--microsoft-peering-config**|object|The Microsoft peering configuration.|microsoft_peering_config|microsoftPeeringConfig|
|**--gateway-manager-etag**|string|The GatewayManager Etag.|gateway_manager_etag|gatewayManagerEtag|
|**--ipv6-express-route-circuit-peering-config-primary-peer-address-prefix-primary-peer-address-prefix**|string|The primary address prefix.|ipv6_express_route_circuit_peering_config_primary_peer_address_prefix_primary_peer_address_prefix|primaryPeerAddressPrefix|
|**--ipv6-express-route-circuit-peering-config-secondary-peer-address-prefix-secondary-peer-address-prefix**|string|The secondary address prefix.|ipv6_express_route_circuit_peering_config_secondary_peer_address_prefix_secondary_peer_address_prefix|secondaryPeerAddressPrefix|
|**--express-route-circuit-peering-config-microsoft-peering-config**|object|The Microsoft peering configuration.|express_route_circuit_peering_config_microsoft_peering_config|microsoftPeeringConfig|
|**--express-route-circuit-peering-state**|choice|The state of peering.|express_route_circuit_peering_state|state|
|**--sub-resource-id**|string|Resource ID.|sub_resource_id|id|

#### <a name="ExpressRouteCrossConnectionPeeringsDelete">Command `az network express-route-cross-connection-peering delete`</a>

##### <a name="ExamplesExpressRouteCrossConnectionPeeringsDelete">Example</a>
```
az network express-route-cross-connection-peering delete --cross-connection-name "<circuitServiceKey>" --peering-name \
"AzurePrivatePeering" --resource-group "CrossConnection-SiliconValley"
```
##### <a name="ParametersExpressRouteCrossConnectionPeeringsDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--cross-connection-name**|string|The name of the ExpressRouteCrossConnection.|cross_connection_name|crossConnectionName|
|**--peering-name**|string|The name of the peering.|peering_name|peeringName|

### group `az network inbound-nat-rule`
#### <a name="InboundNatRulesGet">Command `az network inbound-nat-rule show`</a>

##### <a name="ExamplesInboundNatRulesGet">Example</a>
```
az network inbound-nat-rule show --name "natRule1.1" --load-balancer-name "lb1" --resource-group "testrg"
```
##### <a name="ParametersInboundNatRulesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--load-balancer-name**|string|The name of the load balancer.|load_balancer_name|loadBalancerName|
|**--inbound-nat-rule-name**|string|The name of the inbound nat rule.|inbound_nat_rule_name|inboundNatRuleName|
|**--expand**|string|Expands referenced resources.|expand|$expand|

#### <a name="InboundNatRulesCreateOrUpdate#Create">Command `az network inbound-nat-rule create`</a>

##### <a name="ExamplesInboundNatRulesCreateOrUpdate#Create">Example</a>
```
az network inbound-nat-rule create --inbound-nat-rule-name "natRule1.1" --backend-port 3389 --enable-floating-ip false \
--enable-tcp-reset false --sub-resource-id "/subscriptions/subid/resourceGroups/testrg/providers/Microsoft.Network/load\
Balancers/lb1/frontendIPConfigurations/ip1" --frontend-port 3390 --idle-timeout-in-minutes 4 --protocol "Tcp" \
--load-balancer-name "lb1" --resource-group "testrg"
```
##### <a name="ParametersInboundNatRulesCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--load-balancer-name**|string|The name of the load balancer.|load_balancer_name|loadBalancerName|
|**--inbound-nat-rule-name**|string|The name of the inbound nat rule.|inbound_nat_rule_name|inboundNatRuleName|
|**--id**|string|Resource ID.|id|id|
|**--name**|string|The name of the resource that is unique within the set of inbound NAT rules used by the load balancer. This name can be used to access the resource.|name|name|
|**--protocol**|choice|The reference to the transport protocol used by the load balancing rule.|protocol|protocol|
|**--frontend-port**|integer|The port for the external endpoint. Port numbers for each rule must be unique within the Load Balancer. Acceptable values range from 1 to 65534.|frontend_port|frontendPort|
|**--backend-port**|integer|The port used for the internal endpoint. Acceptable values range from 1 to 65535.|backend_port|backendPort|
|**--idle-timeout-in-minutes**|integer|The timeout for the TCP idle connection. The value can be set between 4 and 30 minutes. The default value is 4 minutes. This element is only used when the protocol is set to TCP.|idle_timeout_in_minutes|idleTimeoutInMinutes|
|**--enable-floating-ip**|boolean|Configures a virtual machine's endpoint for the floating IP capability required to configure a SQL AlwaysOn Availability Group. This setting is required when using the SQL AlwaysOn Availability Groups in SQL server. This setting can't be changed after you create the endpoint.|enable_floating_ip|enableFloatingIP|
|**--enable-tcp-reset**|boolean|Receive bidirectional TCP Reset on TCP flow idle timeout or unexpected connection termination. This element is only used when the protocol is set to TCP.|enable_tcp_reset|enableTcpReset|
|**--sub-resource-id**|string|Resource ID.|sub_resource_id|id|

#### <a name="InboundNatRulesCreateOrUpdate#Update">Command `az network inbound-nat-rule update`</a>

##### <a name="ParametersInboundNatRulesCreateOrUpdate#Update">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--load-balancer-name**|string|The name of the load balancer.|load_balancer_name|loadBalancerName|
|**--inbound-nat-rule-name**|string|The name of the inbound nat rule.|inbound_nat_rule_name|inboundNatRuleName|
|**--id**|string|Resource ID.|id|id|
|**--name**|string|The name of the resource that is unique within the set of inbound NAT rules used by the load balancer. This name can be used to access the resource.|name|name|
|**--protocol**|choice|The reference to the transport protocol used by the load balancing rule.|protocol|protocol|
|**--frontend-port**|integer|The port for the external endpoint. Port numbers for each rule must be unique within the Load Balancer. Acceptable values range from 1 to 65534.|frontend_port|frontendPort|
|**--backend-port**|integer|The port used for the internal endpoint. Acceptable values range from 1 to 65535.|backend_port|backendPort|
|**--idle-timeout-in-minutes**|integer|The timeout for the TCP idle connection. The value can be set between 4 and 30 minutes. The default value is 4 minutes. This element is only used when the protocol is set to TCP.|idle_timeout_in_minutes|idleTimeoutInMinutes|
|**--enable-floating-ip**|boolean|Configures a virtual machine's endpoint for the floating IP capability required to configure a SQL AlwaysOn Availability Group. This setting is required when using the SQL AlwaysOn Availability Groups in SQL server. This setting can't be changed after you create the endpoint.|enable_floating_ip|enableFloatingIP|
|**--enable-tcp-reset**|boolean|Receive bidirectional TCP Reset on TCP flow idle timeout or unexpected connection termination. This element is only used when the protocol is set to TCP.|enable_tcp_reset|enableTcpReset|
|**--sub-resource-id**|string|Resource ID.|sub_resource_id|id|

#### <a name="InboundNatRulesDelete">Command `az network inbound-nat-rule delete`</a>

##### <a name="ExamplesInboundNatRulesDelete">Example</a>
```
az network inbound-nat-rule delete --name "natRule1.1" --load-balancer-name "lb1" --resource-group "testrg"
```
##### <a name="ParametersInboundNatRulesDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--load-balancer-name**|string|The name of the load balancer.|load_balancer_name|loadBalancerName|
|**--inbound-nat-rule-name**|string|The name of the inbound nat rule.|inbound_nat_rule_name|inboundNatRuleName|

### group `az network load-balancer-frontend-ip-configuration`
#### <a name="LoadBalancerFrontendIPConfigurationsList">Command `az network load-balancer-frontend-ip-configuration list`</a>

##### <a name="ExamplesLoadBalancerFrontendIPConfigurationsList">Example</a>
```
az network load-balancer-frontend-ip-configuration list --load-balancer-name "lb" --resource-group "testrg"
```
##### <a name="ParametersLoadBalancerFrontendIPConfigurationsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--load-balancer-name**|string|The name of the load balancer.|load_balancer_name|loadBalancerName|

### group `az network load-balancer-network-interface`
#### <a name="LoadBalancerNetworkInterfacesList">Command `az network load-balancer-network-interface list`</a>

##### <a name="ExamplesLoadBalancerNetworkInterfacesList">Example</a>
```
az network load-balancer-network-interface list --load-balancer-name "lb" --resource-group "testrg"
```
##### <a name="ExamplesLoadBalancerNetworkInterfacesList">Example</a>
```
az network load-balancer-network-interface list --load-balancer-name "lb" --resource-group "testrg"
```
##### <a name="ParametersLoadBalancerNetworkInterfacesList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--load-balancer-name**|string|The name of the load balancer.|load_balancer_name|loadBalancerName|

### group `az network nat-rule`
#### <a name="NatRulesListByVpnGateway">Command `az network nat-rule list`</a>

##### <a name="ExamplesNatRulesListByVpnGateway">Example</a>
```
az network nat-rule list --gateway-name "gateway1" --resource-group "rg1"
```
##### <a name="ParametersNatRulesListByVpnGateway">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name of the VpnGateway.|resource_group_name|resourceGroupName|
|**--gateway-name**|string|The name of the gateway.|gateway_name|gatewayName|

### group `az network network-interface`
#### <a name="NetworkInterfacesGetVirtualMachineScaleSetIpConfiguration">Command `az network network-interface show-virtual-machine-scale-set-ip-configuration`</a>

##### <a name="ExamplesNetworkInterfacesGetVirtualMachineScaleSetIpConfiguration">Example</a>
```
az network network-interface show-virtual-machine-scale-set-ip-configuration --ip-configuration-name "ip1" --name \
"nic1" --resource-group "rg1" --virtual-machine-scale-set-name "vmss1" --virtualmachine-index "2"
```
##### <a name="ParametersNetworkInterfacesGetVirtualMachineScaleSetIpConfiguration">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-machine-scale-set-name**|string|The name of the virtual machine scale set.|virtual_machine_scale_set_name|virtualMachineScaleSetName|
|**--virtualmachine-index**|string|The virtual machine index.|virtualmachine_index|virtualmachineIndex|
|**--network-interface-name**|string|The name of the network interface.|network_interface_name|networkInterfaceName|
|**--ip-configuration-name**|string|The name of the ip configuration.|ip_configuration_name|ipConfigurationName|
|**--expand**|string|Expands referenced resources.|expand|$expand|

### group `az network network-interface-ip-configuration`
#### <a name="NetworkInterfaceIPConfigurationsList">Command `az network network-interface-ip-configuration list`</a>

##### <a name="ExamplesNetworkInterfaceIPConfigurationsList">Example</a>
```
az network network-interface-ip-configuration list --network-interface-name "nic1" --resource-group "testrg"
```
##### <a name="ParametersNetworkInterfaceIPConfigurationsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--network-interface-name**|string|The name of the network interface.|network_interface_name|networkInterfaceName|

#### <a name="NetworkInterfaceIPConfigurationsGet">Command `az network network-interface-ip-configuration show`</a>

##### <a name="ExamplesNetworkInterfaceIPConfigurationsGet">Example</a>
```
az network network-interface-ip-configuration show --ip-configuration-name "ipconfig1" --network-interface-name \
"mynic" --resource-group "testrg"
```
##### <a name="ParametersNetworkInterfaceIPConfigurationsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--network-interface-name**|string|The name of the network interface.|network_interface_name|networkInterfaceName|
|**--ip-configuration-name**|string|The name of the ip configuration name.|ip_configuration_name|ipConfigurationName|

### group `az network network-interface-load-balancer`
#### <a name="NetworkInterfaceLoadBalancersList">Command `az network network-interface-load-balancer list`</a>

##### <a name="ExamplesNetworkInterfaceLoadBalancersList">Example</a>
```
az network network-interface-load-balancer list --network-interface-name "nic1" --resource-group "testrg"
```
##### <a name="ParametersNetworkInterfaceLoadBalancersList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--network-interface-name**|string|The name of the network interface.|network_interface_name|networkInterfaceName|

### group `az network network-interface-tap-configuration`
#### <a name="NetworkInterfaceTapConfigurationsList">Command `az network network-interface-tap-configuration list`</a>

##### <a name="ExamplesNetworkInterfaceTapConfigurationsList">Example</a>
```
az network network-interface-tap-configuration list --network-interface-name "mynic" --resource-group "rg1"
```
##### <a name="ParametersNetworkInterfaceTapConfigurationsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--network-interface-name**|string|The name of the network interface.|network_interface_name|networkInterfaceName|

#### <a name="NetworkInterfaceTapConfigurationsDelete">Command `az network network-interface-tap-configuration delete`</a>

##### <a name="ExamplesNetworkInterfaceTapConfigurationsDelete">Example</a>
```
az network network-interface-tap-configuration delete --network-interface-name "test-networkinterface" \
--resource-group "rg1" --tap-configuration-name "test-tapconfiguration"
```
##### <a name="ParametersNetworkInterfaceTapConfigurationsDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--network-interface-name**|string|The name of the network interface.|network_interface_name|networkInterfaceName|
|**--tap-configuration-name**|string|The name of the tap configuration.|tap_configuration_name|tapConfigurationName|

### group `az network network-watcher`
#### <a name="NetworkWatchersGetAzureReachabilityReport">Command `az network network-watcher get-azure-reachability-report`</a>

##### <a name="ExamplesNetworkWatchersGetAzureReachabilityReport">Example</a>
```
az network network-watcher get-azure-reachability-report --name "nw1" --azure-locations "West US" --end-time \
"2017-09-10T00:00:00Z" --provider-location country="United States" state="washington" --providers "Frontier \
Communications of America, Inc. - ASN 5650" --start-time "2017-09-07T00:00:00Z" --resource-group "rg1"
```
##### <a name="ParametersNetworkWatchersGetAzureReachabilityReport">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the network watcher resource group.|resource_group_name|resourceGroupName|
|**--network-watcher-name**|string|The name of the network watcher resource.|network_watcher_name|networkWatcherName|
|**--provider-location**|object|Parameters that define a geographic location.|provider_location|providerLocation|
|**--start-time**|date-time|The start time for the Azure reachability report.|start_time|startTime|
|**--end-time**|date-time|The end time for the Azure reachability report.|end_time|endTime|
|**--providers**|array|List of Internet service providers.|providers|providers|
|**--azure-locations**|array|Optional Azure regions to scope the query to.|azure_locations|azureLocations|

#### <a name="NetworkWatchersListAvailableProviders">Command `az network network-watcher list-available-provider`</a>

##### <a name="ExamplesNetworkWatchersListAvailableProviders">Example</a>
```
az network network-watcher list-available-provider --name "nw1" --azure-locations "West US" --city "seattle" --country \
"United States" --state "washington" --resource-group "rg1"
```
##### <a name="ParametersNetworkWatchersListAvailableProviders">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the network watcher resource group.|resource_group_name|resourceGroupName|
|**--network-watcher-name**|string|The name of the network watcher resource.|network_watcher_name|networkWatcherName|
|**--azure-locations**|array|A list of Azure regions.|azure_locations|azureLocations|
|**--country**|string|The country for available providers list.|country|country|
|**--state**|string|The state for available providers list.|state|state|
|**--city**|string|The city or town for available providers list.|city|city|

### group `az network p2-s-vpn-gateway`
#### <a name="P2sVpnGatewaysDisconnectP2sVpnConnections">Command `az network p2-s-vpn-gateway disconnect-p2-s-vpn-connection`</a>

##### <a name="ExamplesP2sVpnGatewaysDisconnectP2sVpnConnections">Example</a>
```
az network p2-s-vpn-gateway disconnect-p2-s-vpn-connection --name "p2svpngateway" --resource-group \
"p2s-vpn-gateway-test" --vpn-connection-ids "vpnconnId1" "vpnconnId2"
```
##### <a name="ParametersP2sVpnGatewaysDisconnectP2sVpnConnections">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--p2-s-vpn-gateway-name**|string|The name of the P2S Vpn Gateway.|p2_s_vpn_gateway_name|p2sVpnGatewayName|
|**--vpn-connection-ids**|array|List of p2s vpn connection Ids.|vpn_connection_ids|vpnConnectionIds|

#### <a name="P2sVpnGatewaysGetP2sVpnConnectionHealth">Command `az network p2-s-vpn-gateway get-p2-s-vpn-connection-health`</a>

##### <a name="ExamplesP2sVpnGatewaysGetP2sVpnConnectionHealth">Example</a>
```
az network p2-s-vpn-gateway get-p2-s-vpn-connection-health --gateway-name "p2sVpnGateway1" --resource-group "rg1"
```
##### <a name="ParametersP2sVpnGatewaysGetP2sVpnConnectionHealth">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--gateway-name**|string|The name of the P2SVpnGateway.|gateway_name|gatewayName|

#### <a name="P2sVpnGatewaysGetP2sVpnConnectionHealthDetailed">Command `az network p2-s-vpn-gateway get-p2-s-vpn-connection-health-detailed`</a>

##### <a name="ExamplesP2sVpnGatewaysGetP2sVpnConnectionHealthDetailed">Example</a>
```
az network p2-s-vpn-gateway get-p2-s-vpn-connection-health-detailed --gateway-name "p2svpngateway" --resource-group \
"p2s-vpn-gateway-test" --output-blob-sas-url "https://blobcortextesturl.blob.core.windows.net/folderforconfig/p2sconnec\
tionhealths?sp=rw&se=2018-01-10T03%3A42%3A04Z&sv=2017-04-17&sig=WvXrT5bDmDFfgHs%2Brz%2BjAu123eRCNE9BO0eQYcPDT7pY%3D&sr=\
b" --vpn-user-names-filter "vpnUser1" "vpnUser2"
```
##### <a name="ParametersP2sVpnGatewaysGetP2sVpnConnectionHealthDetailed">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--gateway-name**|string|The name of the P2SVpnGateway.|gateway_name|gatewayName|
|**--vpn-user-names-filter**|array|The list of p2s vpn user names whose p2s vpn connection detailed health to retrieve for.|vpn_user_names_filter|vpnUserNamesFilter|
|**--output-blob-sas-url**|string|The sas-url to download the P2S Vpn connection health detail.|output_blob_sas_url|outputBlobSasUrl|

#### <a name="P2sVpnGatewaysReset">Command `az network p2-s-vpn-gateway reset`</a>

##### <a name="ExamplesP2sVpnGatewaysReset">Example</a>
```
az network p2-s-vpn-gateway reset --gateway-name "p2sVpnGateway1" --resource-group "rg1"
```
##### <a name="ParametersP2sVpnGatewaysReset">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name of the P2SVpnGateway.|resource_group_name|resourceGroupName|
|**--gateway-name**|string|The name of the gateway.|gateway_name|gatewayName|

### group `az network private-link-service`
#### <a name="PrivateLinkServicesListPrivateEndpointConnections">Command `az network private-link-service list-private-endpoint-connection`</a>

##### <a name="ExamplesPrivateLinkServicesListPrivateEndpointConnections">Example</a>
```
az network private-link-service list-private-endpoint-connection --resource-group "rg1" --name "testPls"
```
##### <a name="ParametersPrivateLinkServicesListPrivateEndpointConnections">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--service-name**|string|The name of the private link service.|service_name|serviceName|

#### <a name="PrivateLinkServicesGetPrivateEndpointConnection">Command `az network private-link-service show-private-endpoint-connection`</a>

##### <a name="ExamplesPrivateLinkServicesGetPrivateEndpointConnection">Example</a>
```
az network private-link-service show-private-endpoint-connection --pe-connection-name "testPlePeConnection" \
--resource-group "rg1" --name "testPls"
```
##### <a name="ParametersPrivateLinkServicesGetPrivateEndpointConnection">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--service-name**|string|The name of the private link service.|service_name|serviceName|
|**--pe-connection-name**|string|The name of the private end point connection.|pe_connection_name|peConnectionName|
|**--expand**|string|Expands referenced resources.|expand|$expand|

### group `az network public-ip-address`
#### <a name="PublicIPAddressesListVirtualMachineScaleSetVMPublicIPAddresses">Command `az network public-ip-address list-virtual-machine-scale-set-vm-public-ip-address`</a>

##### <a name="ExamplesPublicIPAddressesListVirtualMachineScaleSetVMPublicIPAddresses">Example</a>
```
az network public-ip-address list-virtual-machine-scale-set-vm-public-ip-address --ip-configuration-name "ip1" \
--network-interface-name "nic1" --resource-group "vmss-tester" --virtual-machine-scale-set-name "vmss1" \
--virtualmachine-index 1
```
##### <a name="ParametersPublicIPAddressesListVirtualMachineScaleSetVMPublicIPAddresses">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-machine-scale-set-name**|string|The name of the virtual machine scale set.|virtual_machine_scale_set_name|virtualMachineScaleSetName|
|**--virtualmachine-index**|string|The virtual machine index.|virtualmachine_index|virtualmachineIndex|
|**--network-interface-name**|string|The network interface name.|network_interface_name|networkInterfaceName|
|**--ip-configuration-name**|string|The IP configuration name.|ip_configuration_name|ipConfigurationName|

#### <a name="PublicIPAddressesGetVirtualMachineScaleSetPublicIPAddress">Command `az network public-ip-address show-virtual-machine-scale-set-public-ip-address`</a>

##### <a name="ExamplesPublicIPAddressesGetVirtualMachineScaleSetPublicIPAddress">Example</a>
```
az network public-ip-address show-virtual-machine-scale-set-public-ip-address --ip-configuration-name "ip1" \
--network-interface-name "nic1" --name "pub1" --resource-group "vmss-tester" --virtual-machine-scale-set-name "vmss1" \
--virtualmachine-index 1
```
##### <a name="ParametersPublicIPAddressesGetVirtualMachineScaleSetPublicIPAddress">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-machine-scale-set-name**|string|The name of the virtual machine scale set.|virtual_machine_scale_set_name|virtualMachineScaleSetName|
|**--virtualmachine-index**|string|The virtual machine index.|virtualmachine_index|virtualmachineIndex|
|**--network-interface-name**|string|The name of the network interface.|network_interface_name|networkInterfaceName|
|**--ip-configuration-name**|string|The name of the IP configuration.|ip_configuration_name|ipConfigurationName|
|**--public-ip-address-name**|string|The name of the public IP Address.|public_ip_address_name|publicIpAddressName|
|**--expand**|string|Expands referenced resources.|expand|$expand|

### group `az network resource-navigation-link`
#### <a name="ResourceNavigationLinksList">Command `az network resource-navigation-link list`</a>

##### <a name="ExamplesResourceNavigationLinksList">Example</a>
```
az network resource-navigation-link list --resource-group "rg1" --subnet-name "subnet" --vnet-name "vnet"
```
##### <a name="ParametersResourceNavigationLinksList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-name**|string|The name of the virtual network.|virtual_network_name|virtualNetworkName|
|**--subnet-name**|string|The name of the subnet.|subnet_name|subnetName|

### group `az network service-association-link`
#### <a name="ServiceAssociationLinksList">Command `az network service-association-link list`</a>

##### <a name="ExamplesServiceAssociationLinksList">Example</a>
```
az network service-association-link list --resource-group "rg1" --subnet-name "subnet" --vnet-name "vnet"
```
##### <a name="ParametersServiceAssociationLinksList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-name**|string|The name of the virtual network.|virtual_network_name|virtualNetworkName|
|**--subnet-name**|string|The name of the subnet.|subnet_name|subnetName|

### group `az network subnet`
#### <a name="SubnetsPrepareNetworkPolicies">Command `az network subnet prepare-network-policy`</a>

##### <a name="ExamplesSubnetsPrepareNetworkPolicies">Example</a>
```
az network subnet prepare-network-policy --service-name "Microsoft.Sql/managedInstances" --resource-group "rg1" --name \
"subnet1" --vnet-name "test-vnet"
```
##### <a name="ParametersSubnetsPrepareNetworkPolicies">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-name**|string|The name of the virtual network.|virtual_network_name|virtualNetworkName|
|**--subnet-name**|string|The name of the subnet.|subnet_name|subnetName|
|**--service-name**|string|The name of the service for which subnet is being prepared for.|service_name|serviceName|
|**--network-intent-policy-configurations**|array|A list of NetworkIntentPolicyConfiguration.|network_intent_policy_configurations|networkIntentPolicyConfigurations|

#### <a name="SubnetsUnprepareNetworkPolicies">Command `az network subnet unprepare-network-policy`</a>

##### <a name="ExamplesSubnetsUnprepareNetworkPolicies">Example</a>
```
az network subnet unprepare-network-policy --resource-group "rg1" --name "subnet1" --service-name \
"Microsoft.Sql/managedInstances" --vnet-name "test-vnet"
```
##### <a name="ParametersSubnetsUnprepareNetworkPolicies">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-name**|string|The name of the virtual network.|virtual_network_name|virtualNetworkName|
|**--subnet-name**|string|The name of the subnet.|subnet_name|subnetName|
|**--service-name**|string|The name of the service for which subnet is being unprepared for.|service_name|serviceName|

### group `az network virtual-hub-bgp-connection`
#### <a name="VirtualHubBgpConnectionDelete">Command `az network virtual-hub-bgp-connection delete`</a>

##### <a name="ExamplesVirtualHubBgpConnectionDelete">Example</a>
```
az network virtual-hub-bgp-connection delete --connection-name "conn1" --resource-group "rg1" --virtual-hub-name \
"hub1"
```
##### <a name="ParametersVirtualHubBgpConnectionDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name of the VirtualHubBgpConnection.|resource_group_name|resourceGroupName|
|**--virtual-hub-name**|string|The name of the VirtualHub.|virtual_hub_name|virtualHubName|
|**--connection-name**|string|The name of the connection.|connection_name|connectionName|

### group `az network virtual-hub-bgp-connection`
#### <a name="VirtualHubBgpConnectionsListAdvertisedRoutes">Command `az network virtual-hub-bgp-connection list-advertised-route`</a>

##### <a name="ExamplesVirtualHubBgpConnectionsListAdvertisedRoutes">Example</a>
```
az network virtual-hub-bgp-connection list-advertised-route --connection-name "peer1" --hub-name "virtualRouter1" \
--resource-group "rg1"
```
##### <a name="ParametersVirtualHubBgpConnectionsListAdvertisedRoutes">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--hub-name**|string|The name of the virtual hub.|hub_name|hubName|
|**--connection-name**|string|The name of the virtual hub bgp connection.|connection_name|connectionName|

#### <a name="VirtualHubBgpConnectionsListLearnedRoutes">Command `az network virtual-hub-bgp-connection list-learned-route`</a>

##### <a name="ExamplesVirtualHubBgpConnectionsListLearnedRoutes">Example</a>
```
az network virtual-hub-bgp-connection list-learned-route --connection-name "peer1" --hub-name "virtualRouter1" \
--resource-group "rg1"
```
##### <a name="ParametersVirtualHubBgpConnectionsListLearnedRoutes">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--hub-name**|string|The name of the virtual hub.|hub_name|hubName|
|**--connection-name**|string|The name of the virtual hub bgp connection.|connection_name|connectionName|

### group `az network virtual-hub-ip-configuration`
#### <a name="VirtualHubIpConfigurationList">Command `az network virtual-hub-ip-configuration list`</a>

##### <a name="ExamplesVirtualHubIpConfigurationList">Example</a>
```
az network virtual-hub-ip-configuration list --resource-group "rg1" --virtual-hub-name "hub1"
```
##### <a name="ParametersVirtualHubIpConfigurationList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name of the VirtualHub.|resource_group_name|resourceGroupName|
|**--virtual-hub-name**|string|The name of the VirtualHub.|virtual_hub_name|virtualHubName|

### group `az network virtual-network`
#### <a name="VirtualNetworksListUsage">Command `az network virtual-network list-usage`</a>

##### <a name="ExamplesVirtualNetworksListUsage">Example</a>
```
az network virtual-network list-usage --resource-group "rg1" --name "vnetName"
```
##### <a name="ParametersVirtualNetworksListUsage">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-name**|string|The name of the virtual network.|virtual_network_name|virtualNetworkName|

### group `az network virtual-network-gateway`
#### <a name="VirtualNetworkGatewaysDisconnectVirtualNetworkGatewayVpnConnections">Command `az network virtual-network-gateway disconnect-virtual-network-gateway-vpn-connection`</a>

##### <a name="ExamplesVirtualNetworkGatewaysDisconnectVirtualNetworkGatewayVpnConnections">Example</a>
```
az network virtual-network-gateway disconnect-virtual-network-gateway-vpn-connection --resource-group \
"vpn-gateway-test" --name "vpngateway" --vpn-connection-ids "vpnconnId1" "vpnconnId2"
```
##### <a name="ParametersVirtualNetworkGatewaysDisconnectVirtualNetworkGatewayVpnConnections">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-name**|string|The name of the virtual network gateway.|virtual_network_gateway_name|virtualNetworkGatewayName|
|**--vpn-connection-ids**|array|List of p2s vpn connection Ids.|vpn_connection_ids|vpnConnectionIds|

#### <a name="VirtualNetworkGatewaysGetVpnclientConnectionHealth">Command `az network virtual-network-gateway get-vpnclient-connection-health`</a>

##### <a name="ExamplesVirtualNetworkGatewaysGetVpnclientConnectionHealth">Example</a>
```
az network virtual-network-gateway get-vpnclient-connection-health --resource-group "p2s-vnet-test" --name "vpnp2sgw"
```
##### <a name="ParametersVirtualNetworkGatewaysGetVpnclientConnectionHealth">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-name**|string|The name of the virtual network gateway.|virtual_network_gateway_name|virtualNetworkGatewayName|

#### <a name="VirtualNetworkGatewaysGetVpnclientIpsecParameters">Command `az network virtual-network-gateway get-vpnclient-ipsec-parameter`</a>

##### <a name="ExamplesVirtualNetworkGatewaysGetVpnclientIpsecParameters">Example</a>
```
az network virtual-network-gateway get-vpnclient-ipsec-parameter --resource-group "rg1" --name "vpngw"
```
##### <a name="ParametersVirtualNetworkGatewaysGetVpnclientIpsecParameters">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-name**|string|The virtual network gateway name.|virtual_network_gateway_name|virtualNetworkGatewayName|

#### <a name="VirtualNetworkGatewaysListConnections">Command `az network virtual-network-gateway list-connection`</a>

##### <a name="ExamplesVirtualNetworkGatewaysListConnections">Example</a>
```
az network virtual-network-gateway list-connection --resource-group "testrg" --name "test-vpn-gateway-1"
```
##### <a name="ParametersVirtualNetworkGatewaysListConnections">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-name**|string|The name of the virtual network gateway.|virtual_network_gateway_name|virtualNetworkGatewayName|

#### <a name="VirtualNetworkGatewaysSetVpnclientIpsecParameters">Command `az network virtual-network-gateway set-vpnclient-ipsec-parameter`</a>

##### <a name="ExamplesVirtualNetworkGatewaysSetVpnclientIpsecParameters">Example</a>
```
az network virtual-network-gateway set-vpnclient-ipsec-parameter --resource-group "rg1" --name "vpngw" --dh-group \
"DHGroup2" --ike-encryption "AES256" --ike-integrity "SHA384" --ipsec-encryption "AES256" --ipsec-integrity "SHA256" \
--pfs-group "PFS2" --sa-data-size-kilobytes 429497 --sa-life-time-seconds 86473
```
##### <a name="ParametersVirtualNetworkGatewaysSetVpnclientIpsecParameters">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-name**|string|The name of the virtual network gateway.|virtual_network_gateway_name|virtualNetworkGatewayName|
|**--sa-life-time-seconds**|integer|The IPSec Security Association (also called Quick Mode or Phase 2 SA) lifetime in seconds for P2S client.|sa_life_time_seconds|saLifeTimeSeconds|
|**--sa-data-size-kilobytes**|integer|The IPSec Security Association (also called Quick Mode or Phase 2 SA) payload size in KB for P2S client..|sa_data_size_kilobytes|saDataSizeKilobytes|
|**--ipsec-encryption**|choice|The IPSec encryption algorithm (IKE phase 1).|ipsec_encryption|ipsecEncryption|
|**--ipsec-integrity**|choice|The IPSec integrity algorithm (IKE phase 1).|ipsec_integrity|ipsecIntegrity|
|**--ike-encryption**|choice|The IKE encryption algorithm (IKE phase 2).|ike_encryption|ikeEncryption|
|**--ike-integrity**|choice|The IKE integrity algorithm (IKE phase 2).|ike_integrity|ikeIntegrity|
|**--dh-group**|choice|The DH Group used in IKE Phase 1 for initial SA.|dh_group|dhGroup|
|**--pfs-group**|choice|The Pfs Group used in IKE Phase 2 for new child SA.|pfs_group|pfsGroup|

#### <a name="VirtualNetworkGatewaysStartPacketCapture">Command `az network virtual-network-gateway start-packet-capture`</a>

##### <a name="ExamplesVirtualNetworkGatewaysStartPacketCapture">Example</a>
```
az network virtual-network-gateway start-packet-capture --filter-data "{\'TracingFlags\': 11,\'MaxPacketBufferSize\': \
120,\'MaxFileSize\': 200,\'Filters\': [{\'SourceSubnets\': [\'20.1.1.0/24\'],\'DestinationSubnets\': \
[\'10.1.1.0/24\'],\'SourcePort\': [500],\'DestinationPort\': [4500],\'Protocol\': 6,\'TcpFlags\': \
16,\'CaptureSingleDirectionTrafficOnly\': true}]}" --resource-group "rg1" --name "vpngw"
```
##### <a name="ExamplesVirtualNetworkGatewaysStartPacketCapture">Example</a>
```
az network virtual-network-gateway start-packet-capture --resource-group "rg1" --name "vpngw"
```
##### <a name="ParametersVirtualNetworkGatewaysStartPacketCapture">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-name**|string|The name of the virtual network gateway.|virtual_network_gateway_name|virtualNetworkGatewayName|
|**--filter-data**|string|Start Packet capture parameters.|filter_data|filterData|

#### <a name="VirtualNetworkGatewaysStopPacketCapture">Command `az network virtual-network-gateway stop-packet-capture`</a>

##### <a name="ExamplesVirtualNetworkGatewaysStopPacketCapture">Example</a>
```
az network virtual-network-gateway stop-packet-capture --sas-url "https://teststorage.blob.core.windows.net/?sv=2018-03\
-28&ss=bfqt&srt=sco&sp=rwdlacup&se=2019-09-13T07:44:05Z&st=2019-09-06T23:44:05Z&spr=https&sig=V1h9D1riltvZMI69d6ihENnFo\
%2FrCvTqGgjO2lf%2FVBhE%3D" --resource-group "rg1" --name "vpngw"
```
##### <a name="ParametersVirtualNetworkGatewaysStopPacketCapture">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-name**|string|The name of the virtual network gateway.|virtual_network_gateway_name|virtualNetworkGatewayName|
|**--sas-url**|string|SAS url for packet capture on virtual network gateway.|sas_url|sasUrl|

#### <a name="VirtualNetworkGatewaysSupportedVpnDevices">Command `az network virtual-network-gateway supported-vpn-device`</a>

##### <a name="ExamplesVirtualNetworkGatewaysSupportedVpnDevices">Example</a>
```
az network virtual-network-gateway supported-vpn-device --resource-group "rg1" --name "vpngw"
```
##### <a name="ParametersVirtualNetworkGatewaysSupportedVpnDevices">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-name**|string|The name of the virtual network gateway.|virtual_network_gateway_name|virtualNetworkGatewayName|

#### <a name="VirtualNetworkGatewaysVpnDeviceConfigurationScript">Command `az network virtual-network-gateway vpn-device-configuration-script`</a>

##### <a name="ExamplesVirtualNetworkGatewaysVpnDeviceConfigurationScript">Example</a>
```
az network virtual-network-gateway vpn-device-configuration-script --device-family "ISR" --firmware-version "IOS 15.1 \
(Preview)" --vendor "Cisco" --resource-group "rg1" --virtual-network-gateway-connection-name "vpngw"
```
##### <a name="ParametersVirtualNetworkGatewaysVpnDeviceConfigurationScript">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-connection-name**|string|The name of the virtual network gateway connection for which the configuration script is generated.|virtual_network_gateway_connection_name|virtualNetworkGatewayConnectionName|
|**--vendor**|string|The vendor for the vpn device.|vendor|vendor|
|**--device-family**|string|The device family for the vpn device.|device_family|deviceFamily|
|**--firmware-version**|string|The firmware version for the vpn device.|firmware_version|firmwareVersion|

### group `az network virtual-network-gateway-connection`
#### <a name="VirtualNetworkGatewayConnectionsGetIkeSas">Command `az network virtual-network-gateway-connection get-ike-sas`</a>

##### <a name="ExamplesVirtualNetworkGatewayConnectionsGetIkeSas">Example</a>
```
az network virtual-network-gateway-connection get-ike-sas --resource-group "rg1" --name "vpngwcn1"
```
##### <a name="ParametersVirtualNetworkGatewayConnectionsGetIkeSas">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-connection-name**|string|The name of the virtual network gateway Connection.|virtual_network_gateway_connection_name|virtualNetworkGatewayConnectionName|

#### <a name="VirtualNetworkGatewayConnectionsStartPacketCapture">Command `az network virtual-network-gateway-connection start-packet-capture`</a>

##### <a name="ExamplesVirtualNetworkGatewayConnectionsStartPacketCapture">Example</a>
```
az network virtual-network-gateway-connection start-packet-capture --filter-data "{\'TracingFlags\': \
11,\'MaxPacketBufferSize\': 120,\'MaxFileSize\': 200,\'Filters\': [{\'SourceSubnets\': [\'20.1.1.0/24\'],\'DestinationS\
ubnets\': [\'10.1.1.0/24\'],\'SourcePort\': [500],\'DestinationPort\': [4500],\'Protocol\': 6,\'TcpFlags\': \
16,\'CaptureSingleDirectionTrafficOnly\': true}]}" --resource-group "rg1" --name "vpngwcn1"
```
##### <a name="ExamplesVirtualNetworkGatewayConnectionsStartPacketCapture">Example</a>
```
az network virtual-network-gateway-connection start-packet-capture --resource-group "rg1" --name "vpngwcn1"
```
##### <a name="ParametersVirtualNetworkGatewayConnectionsStartPacketCapture">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-connection-name**|string|The name of the virtual network gateway connection.|virtual_network_gateway_connection_name|virtualNetworkGatewayConnectionName|
|**--filter-data**|string|Start Packet capture parameters.|filter_data|filterData|

#### <a name="VirtualNetworkGatewayConnectionsStopPacketCapture">Command `az network virtual-network-gateway-connection stop-packet-capture`</a>

##### <a name="ExamplesVirtualNetworkGatewayConnectionsStopPacketCapture">Example</a>
```
az network virtual-network-gateway-connection stop-packet-capture --sas-url "https://teststorage.blob.core.windows.net/\
?sv=2018-03-28&ss=bfqt&srt=sco&sp=rwdlacup&se=2019-09-13T07:44:05Z&st=2019-09-06T23:44:05Z&spr=https&sig=V1h9D1riltvZMI\
69d6ihENnFo%2FrCvTqGgjO2lf%2FVBhE%3D" --resource-group "rg1" --name "vpngwcn1"
```
##### <a name="ParametersVirtualNetworkGatewayConnectionsStopPacketCapture">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--virtual-network-gateway-connection-name**|string|The name of the virtual network gateway Connection.|virtual_network_gateway_connection_name|virtualNetworkGatewayConnectionName|
|**--sas-url**|string|SAS url for packet capture on virtual network gateway.|sas_url|sasUrl|

### group `az network virtual-network-tap`
#### <a name="VirtualNetworkTapsListByResourceGroup">Command `az network virtual-network-tap list`</a>

##### <a name="ExamplesVirtualNetworkTapsListByResourceGroup">Example</a>
```
az network virtual-network-tap list --resource-group "rg1"
```
##### <a name="ParametersVirtualNetworkTapsListByResourceGroup">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|

#### <a name="VirtualNetworkTapsGet">Command `az network virtual-network-tap show`</a>

##### <a name="ExamplesVirtualNetworkTapsGet">Example</a>
```
az network virtual-network-tap show --resource-group "rg1" --tap-name "testvtap"
```
##### <a name="ParametersVirtualNetworkTapsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--tap-name**|string|The name of virtual network tap.|tap_name|tapName|

#### <a name="VirtualNetworkTapsDelete">Command `az network virtual-network-tap delete`</a>

##### <a name="ExamplesVirtualNetworkTapsDelete">Example</a>
```
az network virtual-network-tap delete --resource-group "rg1" --tap-name "test-vtap"
```
##### <a name="ParametersVirtualNetworkTapsDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--tap-name**|string|The name of the virtual network tap.|tap_name|tapName|

### group `az network vpn-connection`
#### <a name="VpnConnectionsStartPacketCapture">Command `az network vpn-connection start-packet-capture`</a>

##### <a name="ExamplesVpnConnectionsStartPacketCapture">Example</a>
```
az network vpn-connection start-packet-capture --gateway-name "gateway1" --filter-data "{\'TracingFlags\': \
11,\'MaxPacketBufferSize\': 120,\'MaxFileSize\': 200,\'Filters\': [{\'SourceSubnets\': [\'20.1.1.0/24\'],\'DestinationS\
ubnets\': [\'10.1.1.0/24\'],\'SourcePort\': [500],\'DestinationPort\': [4500],\'Protocol\': 6,\'TcpFlags\': \
16,\'CaptureSingleDirectionTrafficOnly\': true}]}" --link-connection-names "siteLink1" "siteLink2" --resource-group \
"rg1" --name "vpnConnection1"
```
##### <a name="ExamplesVpnConnectionsStartPacketCapture">Example</a>
```
az network vpn-connection start-packet-capture --gateway-name "gateway1" --link-connection-names "siteLink1" \
"siteLink2" --resource-group "rg1" --name "vpnConnection1"
```
##### <a name="ParametersVpnConnectionsStartPacketCapture">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--gateway-name**|string|The name of the gateway.|gateway_name|gatewayName|
|**--vpn-connection-name**|string|The name of the vpn connection.|vpn_connection_name|vpnConnectionName|
|**--filter-data**|string|Start Packet capture parameters on vpn connection.|filter_data|filterData|
|**--link-connection-names**|array|List of site link connection names.|link_connection_names|linkConnectionNames|

#### <a name="VpnConnectionsStopPacketCapture">Command `az network vpn-connection stop-packet-capture`</a>

##### <a name="ExamplesVpnConnectionsStopPacketCapture">Example</a>
```
az network vpn-connection stop-packet-capture --gateway-name "gateway1" --link-connection-names "vpnSiteLink1" \
"vpnSiteLink2" --sas-url "https://teststorage.blob.core.windows.net/?sv=2018-03-28&ss=bfqt&srt=sco&sp=rwdlacup&se=2019-\
09-13T07:44:05Z&st=2019-09-06T23:44:05Z&spr=https&sig=V1h9D1riltvZMI69d6ihENnFo%2FrCvTqGgjO2lf%2FVBhE%3D" \
--resource-group "rg1" --name "vpnConnection1"
```
##### <a name="ParametersVpnConnectionsStopPacketCapture">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--gateway-name**|string|The name of the gateway.|gateway_name|gatewayName|
|**--vpn-connection-name**|string|The name of the vpn connection.|vpn_connection_name|vpnConnectionName|
|**--sas-url**|string|SAS url for packet capture on vpn connection.|sas_url|sasUrl|
|**--link-connection-names**|array|List of site link connection names.|link_connection_names|linkConnectionNames|

### group `az network vpn-gateway`
#### <a name="VpnGatewaysReset">Command `az network vpn-gateway reset`</a>

##### <a name="ExamplesVpnGatewaysReset">Example</a>
```
az network vpn-gateway reset --gateway-name "vpngw" --resource-group "rg1"
```
##### <a name="ParametersVpnGatewaysReset">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name of the VpnGateway.|resource_group_name|resourceGroupName|
|**--gateway-name**|string|The name of the gateway.|gateway_name|gatewayName|

#### <a name="VpnGatewaysStartPacketCapture">Command `az network vpn-gateway start-packet-capture`</a>

##### <a name="ExamplesVpnGatewaysStartPacketCapture">Example</a>
```
az network vpn-gateway start-packet-capture --gateway-name "vpngw" --filter-data "{\'TracingFlags\': \
11,\'MaxPacketBufferSize\': 120,\'MaxFileSize\': 200,\'Filters\': [{\'SourceSubnets\': [\'20.1.1.0/24\'],\'DestinationS\
ubnets\': [\'10.1.1.0/24\'],\'SourcePort\': [500],\'DestinationPort\': [4500],\'Protocol\': 6,\'TcpFlags\': \
16,\'CaptureSingleDirectionTrafficOnly\': true}]}" --resource-group "rg1"
```
##### <a name="ExamplesVpnGatewaysStartPacketCapture">Example</a>
```
az network vpn-gateway start-packet-capture --gateway-name "vpngw" --resource-group "rg1"
```
##### <a name="ParametersVpnGatewaysStartPacketCapture">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name of the VpnGateway.|resource_group_name|resourceGroupName|
|**--gateway-name**|string|The name of the gateway.|gateway_name|gatewayName|
|**--filter-data**|string|Start Packet capture parameters on vpn gateway.|filter_data|filterData|

#### <a name="VpnGatewaysStopPacketCapture">Command `az network vpn-gateway stop-packet-capture`</a>

##### <a name="ExamplesVpnGatewaysStopPacketCapture">Example</a>
```
az network vpn-gateway stop-packet-capture --gateway-name "vpngw" --sas-url "https://teststorage.blob.core.windows.net/\
?sv=2018-03-28&ss=bfqt&srt=sco&sp=rwdlacup&se=2019-09-13T07:44:05Z&st=2019-09-06T23:44:05Z&spr=https&sig=V1h9D1riltvZMI\
69d6ihENnFo%2FrCvTqGgjO2lf%2FVBhE%3D" --resource-group "rg1"
```
##### <a name="ParametersVpnGatewaysStopPacketCapture">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name of the VpnGateway.|resource_group_name|resourceGroupName|
|**--gateway-name**|string|The name of the gateway.|gateway_name|gatewayName|
|**--sas-url**|string|SAS url for packet capture on vpn gateway.|sas_url|sasUrl|

### group `az network vpn-server-configuration-associated-with-virtual-wan`
#### <a name="VpnServerConfigurationsAssociatedWithVirtualWanList">Command `az network vpn-server-configuration-associated-with-virtual-wan list`</a>

##### <a name="ExamplesVpnServerConfigurationsAssociatedWithVirtualWanList">Example</a>
```
az network vpn-server-configuration-associated-with-virtual-wan list --resource-group "rg1" --virtual-wan-name "wan1"
```
##### <a name="ParametersVpnServerConfigurationsAssociatedWithVirtualWanList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|
|**--virtual-wan-name**|string|The name of the VirtualWAN whose associated VpnServerConfigurations is needed.|virtual_wan_name|virtualWANName|

### group `az network vpn-site-link`
#### <a name="VpnSiteLinksListByVpnSite">Command `az network vpn-site-link list`</a>

##### <a name="ExamplesVpnSiteLinksListByVpnSite">Example</a>
```
az network vpn-site-link list --resource-group "rg1" --vpn-site-name "vpnSite1"
```
##### <a name="ParametersVpnSiteLinksListByVpnSite">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name of the VpnSite.|resource_group_name|resourceGroupName|
|**--vpn-site-name**|string|The name of the VpnSite.|vpn_site_name|vpnSiteName|

#### <a name="VpnSiteLinksGet">Command `az network vpn-site-link show`</a>

##### <a name="ExamplesVpnSiteLinksGet">Example</a>
```
az network vpn-site-link show --resource-group "rg1" --name "vpnSiteLink1" --vpn-site-name "vpnSite1"
```
##### <a name="ParametersVpnSiteLinksGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name of the VpnSite.|resource_group_name|resourceGroupName|
|**--vpn-site-name**|string|The name of the VpnSite.|vpn_site_name|vpnSiteName|
|**--vpn-site-link-name**|string|The name of the VpnSiteLink being retrieved.|vpn_site_link_name|vpnSiteLinkName|

### group `az network vpn-site-link-connection`
#### <a name="VpnSiteLinkConnectionsGet">Command `az network vpn-site-link-connection show`</a>

##### <a name="ExamplesVpnSiteLinkConnectionsGet">Example</a>
```
az network vpn-site-link-connection show --connection-name "vpnConnection1" --gateway-name "gateway1" \
--link-connection-name "Connection-Link1" --resource-group "rg1"
```
##### <a name="ParametersVpnSiteLinkConnectionsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name of the VpnGateway.|resource_group_name|resourceGroupName|
|**--gateway-name**|string|The name of the gateway.|gateway_name|gatewayName|
|**--connection-name**|string|The name of the vpn connection.|connection_name|connectionName|
|**--link-connection-name**|string|The name of the vpn connection.|link_connection_name|linkConnectionName|

### group `az network web-category`
#### <a name="WebCategoriesListBySubscription">Command `az network web-category list`</a>

##### <a name="ExamplesWebCategoriesListBySubscription">Example</a>
```
az network web-category list
```
##### <a name="ParametersWebCategoriesListBySubscription">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|