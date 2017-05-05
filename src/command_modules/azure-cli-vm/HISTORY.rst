.. :changelog:

Release History
===============
2.0.5 (2017-05-05)
++++++++++++++++++
* avail-set: make UD&FD domain counts optional

note: VM commands in sovereign clouds
Please avoid managed disk related features, including the following:
1.       az disk/snapshot/image
2.       az vm/vmss disk
3.       Inside "az vm/vmss create", use "—use-unmanaged-disk" to avoid managed disk
Other commands should work

2.0.4 (2017-04-28)
++++++++++++++++++
* vm/vmss: improve the warning text when generates ssh key pairs

2.0.3 (2017-04-17)
++++++++++++++++++
* vm/vmss: support create from a market place image which requires plan info(#1209)
* Fix bug with `vmss update` and `vm availability-set update`

2.0.2 (2017-04-03)
++++++++++++++++++

* vmss: bug fixes on ip address handling (#2683)
* Fix #2641 (#2670)
* Update storage dependencies (#2654)
* vm: fix the bug that missing fallback default using 'next' (#2624)
* [Compute] Add AppGateway support to VMSS create (#2570)
* [VM/VMSS] Improved disk caching support (#2522)
* VM/VMSS: incorporate credentials validation logic used by portal (#2537)
* Add wait commands and --no-wait support (#2524)
* vm: fix distro check mechanism used by disk encryption (#2511)
* fixed typo in help text (#2519)
* [KeyVault] Command fixes (#2474)
* vm: catch more general exception on querying encryption extension status (#2498)

2.0.1 (2017-03-13)
++++++++++++++++++

* vmss: support * to list instance view across vms (#2467)
* core: support setting default values for common arguments like default resource group, default web, default vm (#2414)
* no dynamic completion on vm create name (#2451)
* VM/VMSS: reuse existing extension instance name on update (#2395)
* Fix bug in vm show. (#2415)
* Add --secrets for VM and VMSS (#2212)
* Allow VM creation with specialized VHD (#2256)
* vm/vmss: move generate_ssh_keys to 'Authentication' group (#2296)

2.0.0 (2017-02-27)
++++++++++++++++++

* GA release
* Fix vmss list-instance-connection-info naming
* Snapshot description update

0.1.2rc2 (2017-02-22)
+++++++++++++++++++++

* VM: fix a casing issue on check os type (#2208)
* Rev compute package to 0.33.rc1 for new API version (#2136)
* Change default VM size to Standard_DS1_v2. (#2181)
* Fix VM names in documentation. (#2183)

0.1.2rc1 (2017-02-17)
+++++++++++++++++++++

* vm/disk: fix bugs in detach (#2138)
* Show commands return empty string with exit code 0 for 404 responses (#2117)
* Disk encryption: Enable/Disable/Show (#2113)
* vm image: do not normalize casing on blob uri (#2126)
* vm/av-set: remove domain count defaults (#2111)
* Move acs commands from vm to acs module (#2098)
* Fix broken name or ids logic in VM/VMSS Create (#2091)
* VM list: avoid add None mac addresss (#2059)
* Use same defaults like portal (#2055)
* VM: command renaming on 'access' related command (#2053)
* Add --custom-data to VM and VMSS create (#2035)
* Improve the default logic on the subnets (#2000)
* Prompts for yes / no use the -y option rather than --force

0.1.1b3 (2017-02-08)
+++++++++++++++++++++

* VM/VMSS: Managed Disk Support
* Enhance vm open-port command with --port and --priority parameters.

0.1.1b2 (2017-01-30)
+++++++++++++++++++++

* VM: generate ssh key file if needed (#1842)
* New VM/VMSS Create (#1849)
* Fix vm doc bug #621, #519 (#1839)
* Add path expansion to file type parameters (#1827)
* Expose flags to show vm ip-address, power state (#1820)
* [ACS] Add validation for SSH key format (#1699)
* Add confirmation prompt to 'vm delete'.
* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* Enable Multi-Cloud VM/VMSS Create.
* [ACS] Add a table transform for acs show to match acs list.
* Fix: az vm boot-diagnostics get-boot-log key1 -> keys[0].value.

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
