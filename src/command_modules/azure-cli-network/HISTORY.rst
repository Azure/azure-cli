.. :changelog:

Release History
===============

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
