.. :changelog:
Release History
===============
2.0.8 (2017-06-13)
^^^^^^^^^^^^^^^^^^
* Remove useless line-too-long suppression
* vm: support attaching data disks on vm create (#3644)
* Improve table output for vm/vmss commands: get-instance-view, list, show, list-usage, etc
* Fix all bad-continuation pylint disables
* support configuring disk caching on attaching a managed disk (#3513)
* core: Create subscription clients with right SDK profile (#3635)
* Fix various pylint disable rules
* Fixed _help.py for get-boot-log (#3616)
* Eliminating too-many-arguments pylint disable rule (#3583)
* output: add support for picking table output fields through jmespath query  (#3581)
* Support attaching existing data disks on vm create
* Fix attribute-defined-outside-init pylint disable rules
* Fix method-hidden pylint disable rule
* Move all existing recording files to latest folder
* fix typos in error message (#3643)
* Remove various pylint disable statements
* VM/VMSS: fixed an issue with name generation that resulted in the create commands not being idempotent.
* [VM/VMSS] Fix idempotency for VM/VMSS create (#3586)
* Remove too-many-nested-blocks (#3469) (#3469)

2.0.7 (2017-05-09)
++++++++++++++++++
* diagnostics: Fix incorrect Linux diagnostics default config with update for LAD v.3.0 extension
* disk: support cross subscription blob import
* disk: add --no-wait flag to disk create, update, and delete.
* disk: add `az disk wait` command.
* BC: disk: add confirmation prompt to `az disk delete`.
* vm: support license type on create
* BC: vm open-port: command always returns the NSG. Previously it returned the NIC or Subnet.
* vm: fix "vm extension list" crash if the VM has no extensions
* vmss: update arg description for 'vmss delete-instances --instance-ids'
* vmss: hide arg 'vmss show --ids', which is not supposed to work because of 'instance-id' arg
* BC: vmss list-instance-connection-info: include instance IDs in the output
* vm/vmss diagnostics: provide protected settings samples, handle extension major version upgrade, etc.
* disk/snapshot/image: expose '--tags' in the create command
* vmss: provides default for '--app-gateway-subnet-address-prefix' when creating a new vnet
* vm: support configuring disk caching on attaching a managed disk

2.0.6 (2017-05-09)
++++++++++++++++++
* Minor fixes.

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
