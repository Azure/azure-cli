.. :changelog:

Release History
===============

unreleased
+++++++++++++++++++
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
