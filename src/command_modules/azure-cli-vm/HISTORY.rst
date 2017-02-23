.. :changelog:

Release History
===============

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
