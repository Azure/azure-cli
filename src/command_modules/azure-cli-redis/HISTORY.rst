.. :changelog:

Release History
===============

0.4.1
+++++
* Minor fixes.

0.4.0
++++++
* Added commands for managing firewall-rules (create, update, delete, show, list)
* Added commands for managing server-link (create, delete, show, list)
* Added commands for managing patch-schedule (create, update, delete, show)
* `az redis create` : Support for Availability Zones and Minimum TLS Version
* BREAKING CHANGE: Removed 'az redis update-settings' and 'az redis list-all' command
* BREAKING CHANGE: Parameter for redis create: 'tenant settings' is not accepted in key[=value] format
* Added warning message for deprecating 'az redis import-method' command.

0.3.2
+++++
* Minor fixes

0.3.1
+++++
* Minor fixes

0.3.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.

0.2.14
++++++
* Minor fixes.

0.2.13
++++++
* Deprecated `redis patch-schedule patch-schedule show` in favor of `redis patch-schedule show`.
* Deprecated `redis list-all`. This functionality has been folded into `redis list`.
* Deprecated `redis import-method` in favor of `redis import`.
* Added support for `--ids` to various commands.

0.2.12
++++++
* `sdist` is now compatible with wheel 0.31.0

0.2.11
++++++
* Update for CLI core changes.

0.2.10
++++++
* minor fixes

0.2.9 (2017-09-22)
++++++++++++++++++
* minor fixes

0.2.8 (2017-08-28)
++++++++++++++++++
* minor fixes

0.2.7 (2017-07-07)
++++++++++++++++++
* minor fixes

0.2.6 (2017-06-21)
++++++++++++++++++
* No changes.

0.2.5 (2017-06-13)
++++++++++++++++++
* Minor fixes.

0.2.4 (2017-05-30)
++++++++++++++++++++
* Minor fixes.

0.2.3 (2017-05-09)
++++++++++++++++++++
* Minor fixes.

0.2.2 (2017-05-05)
++++++++++++++++++++
* Minor fixes.

0.2.1 (2017-04-28)
++++++++++++++++++++
* New packaging system

0.2.0 (2017-04-17)
++++++++++++++++++++
* Adding update command which also adds the ability to scale for redis cache
* Deprecates the 'update-settings' command.

0.1.1b3 (2017-02-22)
++++++++++++++++++++

* Documentation updates.

0.1.1b2 (2017-01-30)
++++++++++++++++++++

* Support Python 3.6.

0.1.1b1 (2017-01-17)
++++++++++++++++++++

* Preview release (no source code changes since previous version).

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
