.. :changelog:

Release History
===============

unreleased
+++++++++++++++++++
* `vmss create`: Fixed issue where supplying `--app-gateway ID` would fail.
* `vm create`: Added `--asgs` support.
* `vm run-command`: support to run commands on remote VMs
* `vmss encryption`: (PREVIEW) support vmss disk encryptions
* `vm perform-maintenance`: support to perform maintenance on a vm

2.0.14 (2017-09-11)
+++++++++++++++++++
* msi: don't assign access unless `--scope` is provided
* msi: use the same extension naming as portal does
* msi: remove the useless `subscription` from the `vm/vmss create` commands output
* `vm/vmss create`: fix a bug that the storage sku is not applied on data disks coming with an image
* `vm format-secret`: Fix issue where `--secrets` would not accept newline separated IDs.

2.0.13 (2017-08-28)
+++++++++++++++++++
* `vmss get-instance-view`: Fix issue where extra, erroneous information was displayed when using `--instance-id *`
* `vmss create`: Added support for `--lb-sku`
* `vm/vmss create`: remove human names from the admin name blacklist
* `vm/vmss create`: fix issue where the command would throw an error if unable to extract plan information from an image. 
* `vmss create`: fix a crash when create a scaleset with an internal LB
* `vm availability-set create`: Fix issue where --no-wait argument did not work.

2.0.12 (2017-08-11)
+++++++++++++++++++
* availability-set: expose fault domain count on convert
* vm: expose 'az vm list-skus' command
* vm/vmss: support to assign identity w/o creating role assignments
* vm: apply storage sku on attaching data disks
* vm: remove default os-disk name and storage SKU when using managed disks.

2.0.11 (2017-07-27)
+++++++++++++++++++
* vmss: support configuring nsg
* vmss: fix a bug that dns server is not configured right.
* vm/vmss: support managed service identity
* `vmss create`: Fix issue where creating with existing load balancer required `--backend-pool-name`.
* `vm image create`: make datadisk's lun start with 0

2.0.10 (2017-07-07)
+++++++++++++++++++
* vm/vmss: use newer api-version of "2017-03-30"
* BC: 'sku.managed' is removed from 'az vm availability-set show' (use sku.name instead)
* `vmss create`: add arguments `--app-gateway-capacity` and `--app-gateway-sku`.
* `vm/vmss create`: if --admin-password is specified for Linux images, automatically will change from SSH authentication
  to password without needing `--authentication-type password` explicitly.
* `vm/vmss create`: added information statements that can be shown using --debug
* `vm/vmss create`: added client-side validation where certain parameters were previously just ignored.
* `vmss create`: support public ip per instance, instance custom domain name, custom dns servers


2.0.9 (2017-06-21)
++++++++++++++++++
* vm/vmss: lower thread number used for 'vm image list --all' to avoid exceeding the OS opened file limits  
* diagnostics: Fix a typo in default Linux Diagnostic extension config
* vmss create: fix failure when running with --use-unmanaged-disk

2.0.8 (2017-06-13)
++++++++++++++++++
* vm: support attaching data disks on vm create (#3644)
* Improve table output for vm/vmss commands: get-instance-view, list, show, list-usage, etc
* support configuring disk caching on attaching a managed disk (#3513)
* Support attaching existing data disks on vm create
* VM/VMSS: fixed an issue with name generation that resulted in the create commands not being idempotent.

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
