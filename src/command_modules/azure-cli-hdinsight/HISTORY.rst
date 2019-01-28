.. :changelog:

Release History
===============
0.4.0
+++++
*	Change OMS group to monitor
  *	Change the 'oms' command group to 'monitor'
  *	Change all instances of "Operations Management Suite (OMS)" in descriptions to "Azure Monitor logs integration”
  *	Autocomplete workspace id and key (remove workspace key parameter)

* ESP parameters updates
  *	cluster-admin-account completer
  *	cluster-users-group-dns completer
  *	cluster-users-group-dns parameter should be mandatory for --esp clusters

Other changes:
*	Make the "--http-password -p" a required parameter
*	Add time out for all existing argument auto-completers.
*	Add time out for transforming recourse name to resource id.
*	Allow auto-completers to select resources from any resource group. It can be a different resource group that '-g' specifies.

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
