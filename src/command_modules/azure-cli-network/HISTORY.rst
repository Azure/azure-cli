.. :changelog:

Release History
===============

2.3.3
+++++
* `vpn-connection create/update`: Add `--express-route-gateway-bypass` argument.
* `express-route`: Port command groups from `express-route` extensions.
* `express-route`: Added `express-route gateway` and `express-route port` command groups.
* `express-route peering create/update`: Added argument `--legacy-mode`.
* `express-route create/update`: Added argument `--allow-classic-operations` and `--express-route-port`.
* `vnet-gateway create/update`: Add `--gateway-default-site` argument.
* `vnet-gateway`: Added `ipsec-policy` commands.

2.3.2
+++++
* `dns zone export`: Ensure exported CNAMEs are FQDNs.
* `nic ip-config address-pool add/remove`: Add `--gateway-name` to support application gateway backend address pools.
* `network watcher flow-log configure`: Add arguments `--traffic-analytics`, `--workspace` to support traffic analytics through a Log Analytics workspace.
* `lb inbound-nat-pool create/update`: Add arguments `--idle-timeout`, `--floating-ip`.

2.3.1
++++++
* `express-route update`: Fix issue where `--bandwidth` argument was ignored.
* `ddos-protection update`: Fix issue with set comprehension causing stack trace.

2.3.0
+++++
* `traffic-manager profile create/update`: Add support for `--custom-headers` and `--status-code-ranges`. Add support for new routing types: Subnet and Multivalue.
* `traffic-manager endpoint create/update`: Add support for `--custom-headers` and `--subnets`.
* `ddos-protection update`: Fix issue where supplying `--vnets ""` to remove vnets caused a strack trace.

2.2.11
++++++
* `watcher flow-log configure`: Add support for `--format` and `--log-version`.
* `dns zone update`: Finished issue where using "" to clear resolution and registration VNets didn't work.

2.2.10
++++++
* `application-gateway waf-config set`: Added `--exclusion` argument to support WAF exclusions.

2.2.9
+++++
* `application-gateway`: Added `root-cert` subcommands to handle trusted root certifcates.
* `application-gateway create/update`:
   Added `--min-capacity` for configuring autoscale on v2 app gateways.
   Added `--custom-error-pages` for configuring custom error pages.
* `application-gateway create`: Added `--zones` for availability zone support.
* `application-gateway waf-config set`: Added arguments `--file-upload-limit`, `--max-request-body-size` and `--request-body-check`.

2.2.8
+++++
* Deprecated `network interface-endpoint` command names in favor of `network private-endpoint`.
* `express-route peering connection create`: Fix issue where `--peer-circuit` would not accept an ID.
* `public-ip create`: Fix issue where `--ip-tags` did not work correctly.

2.2.7
+++++
* `nic create` - Add `--app-gateway-address-pools` and `--gateway-name` arguments to support adding application
  gateway backend address pools to a NIC.
* `nic ip-config create/update` - Add `--app-gateway-address-pools` and `--gateway-name` arguments to support adding application
  gateway backend address pools to a NIC.


2.2.6
+++++
* Fix `network dns zone create`. Command succeeds even if the user has configured a default location. See #6052.
* `network vnet peering create`: Deprecated `--remote-vnet-id`. Added --remote-vnet which accepts a name or ID.
* `network vnet create`: Added support for multiple subnet prefixes with `--subnet-prefixes`.
* `network vnet subnet create/update`: Added support for multiple subnet prefixes with `--address-prefixes`.
* `network application-gateway create`: Fixed logic that prevented creating gateways with WAF_v2 or Standard_v2 SKU.
* `network vnet subnet update`: Added `--service-endpoint-policy` convenience argument.

2.2.5
+++++
* Add `network public-ip prefix` commands to support public IP prefixes features.
* Add `network service-endpoint` commands to support service endpoint policy features.
* Add `network lb outbound-rule` commands to support creation of Standard Load Balancer outbound rules.
* Add `--public-ip-prefix` to `network lb frontend-ip create/update` to support frontend IP configurations using public IP prefixes.
* Add `--enable-tcp-reset` to `network lb rule/inbound-nat-rule/inbound-nat-pool create/update`.
* Add `--disable-outbound-snat` to `network lb rule create/update`.
* Allow `network watcher flow-log show/configure` to be used with classic NSGs.
* Add `network watcher run-configuration-diagnostic` command.
* Fix `network watcher test-connectivity` command and add `--method`, `--valid-status-codes` and `--headers` properties.
* `network express-route create/update`: Add `--allow-global-reach` flag.
* `network vnet subnet create/update`: Add support for `--delegation`.
* Added `network vnet subnet list-available-delegations` command.
* `network traffic-manager profile create/update`: Added support for `--interval`, `--timeout` and `--max-failures` for Monitor configuration.
  Deprecated options `--monitor-path`, `--monitor-port` and `--monitor-protocol` in favor of `--path`, `--port`, `--protocol`.
* `network lb frontend-ip create/update`: Fixed the logic for setting private IP allocation method. If a private IP address is provided, the
  allocation will be static. If no private IP address is provided, or empty string is provided for private IP address, allocation is dynamic.
* `dns record-set * create/update`: Add support for `--target-resource`.
* Add `network interface-endpoint` commands to query interface endpoint objects.
* Add `network profile show/list/delete` for partial management of network profiles.
* Add `network express-route peering connection` commands to manage peering connections between ExpressRoutes.

2.2.4
+++++
* `network application-gateway ssl-policy predefined show`: exception handling to exit with code 3 upon a missing resource for consistency

2.2.3
+++++
* Minor fixes

2.2.2
+++++
* `dns`: Added dns support to 2017-03-09-profile for Azure Stack 

2.2.1
++++++
* Minor fixes

2.2.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.
* `network nic create/update/delete`: Add `--no-wait` support.
* Added `network nic wait`.
* `network vnet subnet list`: Argument `--ids` is deprecated.
* `network vnet peering list`: Argument `--ids` is deprecated.
* `network nsg rule list`: Added `--include-default` flag to include default security rules in the output.

2.1.5
++++++
* `network dns zone import`: Fix issue where record types were case-sensitive. [#6602](https://github.com/Azure/azure-cli/issues/6602)

2.1.4
++++++
* `network lb probe create`: support `Https` protocol [#6571](https://github.com/Azure/azure-cli/issues/6571)
* `network traffic-manager endpoint create/update`: Fix issue where `--endpoint-status` was case sensitive. [#6502](https://github.com/Azure/azure-cli/issues/6502)

2.1.3
++++++
* `network vnet peering`: a few improvements

2.1.2
++++++
* `network watcher show-topology`: Fix issue where command would not work with vnet and/or subnet name. [#6326](https://github.com/Azure/azure-cli/issues/6326)

2.1.1
++++++
* `network watcher`: Fix issue where certain commands would claim Network Watcher is not enabled for regions when it actually is. [#6264](https://github.com/Azure/azure-cli/issues/6264)

2.1.0
++++++
* BREAKING CHANGE: `express-route auth list`, `express-route peering list`, `nic ip-config list`
                   `nsg rule list`, `route-filter rule list`, `route-table route list`,
                   `traffic-manager endpoint list`: Removed the `--ids` parameter.

2.0.28
++++++
* `application-gateway create`: Fix issue where tags could not be set. [#5936](https://github.com/Azure/azure-cli/issues/5936)
* `application-gateway http-settings create/update`: Add convenience argument `--auth-certs` to attach authentication certificates. [#4910](https://github.com/Azure/azure-cli/issues/4910)
* `ddos-protection`: Added new commands to create DDoS protection plans .
* `vnet create/update`: Added support for `--ddos-protection-plan` to associate a VNet to a DDoS protection plan.
* `network route-table create/update`: Fix issue with `--disable-bgp-route-propagation` flag.
* `network lb create/update`: Removed dummy arguments `--public-ip-address-type` and `--subnet-type`.
* `sdist` is now compatible with wheel 0.31.0

2.0.27
++++++
* `network dns zone import`: Support for importing of TXT records with RFC 1035 escape sequences.
* `network dns zone export`: Support for exporting of TXT records with RFC 1035 escape sequences.
* `network dns record-set txt add-record`: Support for TXT records with RFC 1035 escape sequences.

2.0.26
++++++
* `network dns zone create/update`: Adding support for Private DNS zones.

2.0.25
++++++
* BREAKING CHANGE: `route-filter rule create`: The `--tags` parameter is no longer supported.
* Support Autorest 3.0 based SDKs
* Fix issues with update commands in `express-route`, `nsg rule`, `public-ip`, `traffic manager profile` and `vnet-gateway` where some parameters erroneously had default values.
* `network watcher`: Added `connection-monitor` commands.
* `network watcher show-topology`: Added support to target `--vnet` and `--subnet`.

2.0.24
++++++
* `network vnet-gateway vpn-client generate`: Fix missing client issue.

2.0.23
++++++
* `network public-ip create`: Fix `--tags` option.
* `network lb create`: Fix `--tags` option.
* `network local-gateway create`: Fix `--tags` option.
* `network nic create`: Fix `--tags` option.
* `network vnet-gateway create`: Fix `--tags` option.
* `network vpn-connection create`: Fix `--tags` option.

2.0.22
++++++
* `application-gateway create`: `--cert-password` protected using secureString.
* `application-gateway update`: Fix issue where `--sku` erroneously applied a default value.
* `vpn-connection create`: `--shared-key` and `--authorization-key` protected using secureString.
* `asg create`: Fix missing client issue.
* `dns zone export`: Fix issue with exported names. Add `--file-name/-f` parameter.
                     Fix issue where long TXT records were incorrectly exported.
                     Fix issue where quoted TXT records were incorrectly exported without escaped quotes.
* `dns zone import`: Fix issue where certain records were imported twice.
* Restored `vnet-gateway root-cert` and `vnet-gateway revoked-cert` commands.

2.0.21
++++++
* `vnet-gateway update`: Fix issue when trying to change to/from active-standby mode.
* `application-gateway create/update`: Add support for HTTP2.

2.0.20
++++++
* Update for CLI core changes.

2.0.19
++++++
* `route-table create/update`: Add support for `--disable-bgp-route-propagation`.
* `public-ip create/update`: Add support for `--ip-tags`

2.0.18
++++++
* `dns`: Add support for CAA records.
* `traffic-manager profile update`: Fix issue where profiles with endpoints could not be updated.
* `vnet update`: Fix issue where `--dns-servers` didn't work depending on how the VNET was created (ARM deployment).
* `dns zone import`: Fix issue where relative names were incorrectly imported.

2.0.17
++++++
* minor fixes

2.0.16 (2017-10-09)
+++++++++++++++++++
* `application-gateway address-pool create`: `--server` argument is not optional to allow creation of empty address pools.
* `traffic-manager`: Updates to support latest features.


2.0.15 (2017-09-22)
+++++++++++++++++++
* `lb/public-ip`: Add availability zone support.
* `express-route`: Add support for IPv6 Microsoft Peering
* Add `asg` application security group commands.
* `nic create`: Added `--application-security-groups` support.
* `nic ip-config create/update`: Added `--application-security-groups` support.
* `nsg rule create/update`: Added `--source-asgs` and `--destination-asgs` support.
* `vnet create/update`: Added `--ddos-protection` and `--vm-protection` support.
* Added command: `vnet-gateway vpn-client show-url`

2.0.14 (2017-09-11)
+++++++++++++++++++
* `vnet-gateway`: Added commands `list-bgp-peer-status`, `list-learned-routes` and `list-advertised-routes`
* `vnet-gateway`: Added command `vpn-client generate`.


2.0.13 (2017-08-28)
+++++++++++++++++++
* BC `vnet list-private-access-services`: renamed to `vnet list-endpoint-services`
* BC `vnet subnet create/update`: renamed `--private-access-services` to `--service-endpoints`
* `nsg rule create/update`: Add support for multiple IP ranges and port ranges.
* `lb create`: Added support for SKU.
* `public-ip create`: Added support for SKU.

2.0.12 (2017-08-11)
+++++++++++++++++++
* `lb`: fixed issue where the certain child resource names did not resolve correctly when omitted
* `application-gateway {subresource} delete`: Fixed issue where `--no-wait` was not honored.
* `application-gateway http-settings update`: Fix issue where `--connection-draining-timeout` could not be turned off.
* `[Network] Fix error - unexpected keyword argument 'sa_data_size_kilobyes'` : Fix where `az network vpn-connection ipsec-policy add` unexpected keyword argument 'sa_data_size_kilobyes'

2.0.11 (2017-07-27)
+++++++++++++++++++
* Added `list-private-access-services` command
* `vnet subnet create/update`: Added `--private-access-services` argument.
* `application-gateway redirect-config create`: Fix issue where create command would fail. Fix issue where `--no-wait`
  would not work with update command.
* `application-gateway url-path-map rule create`: Fix issue where certain parameters which should accept names or IDs
  would only accept IDs.

2.0.10 (2017-07-07)
+++++++++++++++++++
* `application-gateway address-pool create/update`: fix bug when using the `--servers` argument.
* `application-gateway`: add `redirect-config` commands
* `application-gateway ssl-policy`: add `list-options`, `predefined list` and `predefined show` commands
* `application-gateway ssl-policy set`: new arguments `--name`, `--cipher-suites`, `--min-protocol-version`
* `application-gateway http-settings create/update`: new arguments `--host-name-from-backend-pool`, `--affinity-cookie-name`,
  `--enable-probe`, `--path`
* `application-gateway url-path-map create/update`: new arguments `--default-redirect-config`, `--redirect-config`
* `application-gateway url-path-map rule create`: new argument `--redirect-config`
* `application-gateway url-path-map rule delete`: add support for `--no-wait`
* `application-gateway probe create/update`: new arguments `--host-name-from-http-settings`, `--min-servers`, `--match-body`, `--match-status-codes`
* `application-gateway rule create/update`: new argument `--redirect-config`


2.0.9 (2017-06-21)
++++++++++++++++++
* `nic create/update`: Add support for `--accelerated-networking`.
* BC `nic create`: Remove non-functional `--internal-dns-name-suffix` argument.

2.0.8 (2017-06-13)
++++++++++++++++++
* `nic update/create`: Add support for --dns-servers.
* `local-gateway create`: fix bug where --local-address-prefixes was ignored.
* `vnet update`: Add support for --dns-servers.

2.0.7 (2017-05-30)
++++++++++++++++++

* `express-route peering create`: fix bug when creating a peering without route filtering.
* `express-route update`: fix bug where --provider and --bandwidth arguments did not work.
* `network watcher show-topology`: Fix bug with location defaulting logic.
* `network list-usages`: improve output for TSV and table format.
* `application-gateway http-listener create`: Default frontend IP if only one exists.
* `application-gateway rule create`: Default address pool, HTTP settings, and HTTP listener if
   only one exists.
* `lb rule create`: Default frontend IP and backend pool if only one exists.
* `lb inbound-nat-rule create`: Default frontend IP if only one exists.

2.0.6 (2017-05-09)
++++++++++++++++++

* Minor fixes.

2.0.5 (2017-05-05)
++++++++++++++++++

* Add `network watcher test-connectivity` command.
* Add support for `--filters` parameter for `network watcher packet-capture create`.

2.0.4 (2017-04-28)
++++++++++++++++++

* Add support for Application Gateway connection draining.
* Add support for Application Gateway WAF rule set configuration.
* Add support for ExpressRoute route filters and rules.
* Add support for TrafficManager geographic routing.
* Add support for VPN connection policy-based traffic selectors.
* Add support for VPN connection IPSec policies.
* Fix bug with `vpn-connection create` when using the `--no-wait` or `--validate` parameters.

2.0.3 (2017-04-17)
++++++++++++++++++

* Add support for active-active VNet gateways
* Remove nulls values from output of `network vpn-connection list/show` commands.
* BC: Fix bug in the output of `vpn-connection create`
* Fix bug where '--key-length' argument of 'vpn-connection create' was not parsed correctly.
* Fix bug in `dns zone import` where records were not imported correctly.
* Fix bug where `traffic-manager endpoint update` did not work.
* Add 'network watcher' preview commands.

2.0.2 (2017-04-03)
++++++++++++++++++

* [Network] Convert Load Balancer and App Gateway Create to Dynamic Templates (#2668)
* Fix format bug. (#2549)
* Add wait commands and --no-wait support (#2524)
* [KeyVault] Command fixes (#2474)

2.0.1 (2017-03-13)
++++++++++++++++++

* Fix: 'None' already exists. Replacing values. (#2390)
* Convert network creates to use SDK (#2371)
* Convert PublicIP Create to use SDK (#2294)
* Convert VNet Create to use SDK (#2269)


2.0.0 (2017-02-27)
++++++++++++++++++

* GA release.


0.1.2rc2 (2017-02-22)
+++++++++++++++++++++

* Fix VPN connection create shared-key validator.
* Add delete confirmation for DNS record-set delete.
* Fix bug with local address prefixes.
* Documentation updates.


0.1.2rc1 (2017-02-17)
+++++++++++++++++++++

* DNS/Application-Gateway Fixes
* Show commands return empty string with exit code 0 for 404 responses (#2117)'
* DNS Zone Import/Export (#2040)
* Restructure DNS Commands (#2112)

0.1.1b2 (2017-01-30)
+++++++++++++++++++++

* Table output for 'network dns record-set list'.
* Prompt confirmation for 'network dns zone delete'.
* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

**Breaking changes**

Renames --sku-name to --sku and removes the --sku-tier parameter. It is parsed from the SKU name.

For the application-gateway {subresource} list commands, changes the alias for the application gateway name from --name/-n to --gateway-name.

Renames vpn-gateway commands to vnet-gateway commands for consistency with the SDK, Powershell, and the VPN connection commands.

Adds 'name-or-id' logic to vpn-connection create so that you can specify the appropriate resource name instead of only the ID. Renames the related arguments to omit -id.

Removes --enable-bgp from the vnet-gateway create command.

* Improvements to ExpressRoute update commands
* RouteTable/Route command updates
* VPN connection fixes
* VNet Gateway Fixes and Enhancements
* Application Gateway Commands and Fixes
* DNS Fixes
* DNS Record Set Create Updates
* ExpressRoute peering client-side validation

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
