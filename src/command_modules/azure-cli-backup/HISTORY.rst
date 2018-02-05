.. :changelog:

Release History
===============

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
