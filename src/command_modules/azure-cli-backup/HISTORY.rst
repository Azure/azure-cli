.. :changelog:

Release History
===============

1.2.1
+++++
* `backup vault backup-properties show`: exception handling to exit with code 3 upon a missing resource for consistency.

1.2.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.

1.1.2
++++++
* Minor fixes.

1.1.1
+++++
* `sdist` is now compatible with wheel 0.31.0

1.1.0
+++++
* Added new command 'az backup protection isenabled-for-vm'. This command can be used to check if a VM is backed up by any vault in the subscription.
* Enabled --ids for vault_name and resource_group parameters for the following commands:
  az backup container show
  az backup item set-policy
  az backup item show
  az backup job show
  az backup job stop
  az backup job wait
  az backup policy delete
  az backup policy get-default-for-vm
  az backup policy list-associated-items
  az backup policy set
  az backup policy show
  az backup protection backup-now
  az backup protection disable
  az backup protection enable-for-vm
  az backup recoverypoint show
  az backup restore files mount-rp
  az backup restore files unmount-rp
  az backup restore restore-disks
  az backup vault delete
  az backup vault show
* 'name' parameters now accept the name format as output from the show commands.

1.0.7
+++++
* Support Autorest 3.0 based SDKs

1.0.6
+++++
* New feature: 'az backup item list' command now has '--container-name' parameter as optional instead of mandatory and output contains item health details.
* New feature: Added original storage account option in 'az backup restore restore-disks' command.
* Bugs fixed: VM and vault location check must be case insensitive in 'az backup protection enable-for-vm' command.

1.0.5
+++++
* When a non-existent name is supplied for a container, commands will not fail with a stack trace. Partially fixes #4502.
* az backup item list update: 'Health Status' of an item is now visible in the default table view.

1.0.4
+++++
* Minor fixes.

1.0.3
+++++
* Minor fixes.

1.0.2
+++++
* no changes

1.0.1 (2017-09-22)
++++++++++++++++++
* Preview release.
