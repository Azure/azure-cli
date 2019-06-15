.. :changelog:

Release History
===============
0.3.5
+++++
* Support for using `--ssh-public-key` parameter in `hdinsight create` command.

0.3.4
+++++
* Upgrade azure-mgmt-storage from 3.1.1 to 3.3.0

0.3.3
+++++
* Minor fixes.

0.3.2
+++++
* `create`: added the `--storage-account-managed-identity` parameter to support ADLS Gen2 MSI.

0.3.1
+++++
* Minor fixes.

0.3.0
+++++

* BREAKING CHANGE: `create`, `application create`: Removed the `--virtual-network` and `--subnet-name` parameters.
                   `create`: Change the `--storage-account` to accept name or id of storage account instead of blob endpoints.
* `create`: added the `--vnet-name` and `--subnet-name` parameters.
* `create`: added support for Enterprise Security Package and disk encryption
* Added `rotate-disk-encryption-key` command
* Added `update` command

0.2.0
+++++

* Add commands for managing applications
* Add commands for managing script actions
* Add commands for managing Operations Management Suite (OMS)
* `hdinsight list-usage`: support to list regional usages
* `hdinsight create`: remove default cluster type

0.1.0
+++++

* Initial release of module.
