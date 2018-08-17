.. :changelog:

Release History
===============

0.3.1
+++++
* Increment DPS mgmt SDK requirement
* Fix internal breaking changes for SDK usage patterns
* Apply work around (back rev API) for assocating a linked-hub due to swagger/sdk mismatch with API.
* Update tests and DPS recording

0.3.0
+++++
* BREAKING CHANGE: Removed deprecated commands which have moved to the iot extension
* Updated elements to not assume azure-devices.net domain

0.2.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.

0.1.22
++++++
* Minor fixes.

0.1.21
++++++

* Adds support for creating Basic Tier IoT Hubs.
* Updates to Azure SDK 0.5.0

0.1.20
++++++

* Minor fixes to compat with msrest 0.4.28

0.1.19
++++++

* `sdist` is now compatible with wheel 0.31.0

0.1.18
++++++
* Support Autorest 3.0 based SDKs

0.1.17
++++++
* iot dps access policy create/update: Fixes issue where the command would occasionally return a 'not found' error on success. Added `--no-wait` support.
* iot dps linked-hub create/update: Fixes issue where the command would occasionally return a 'not found' error on success. Added `--no-wait` support.
* iot hub create: Allow specifying numbers of partitions during creation.
* Minor fixes.

0.1.16
++++++
* Added support for device provisioning service
* Added deprecation messages in commands and command help.
* Added IoT run once check to warn users about the availability of the IoT Extension.

0.1.15
++++++
* Minor fixes.

0.1.14
++++++
* Adds support for certificate authorities (CA) and certificate chains.
* Minor fixes.

0.1.13
++++++
* minor fixes

0.1.12 (2017-09-22)
+++++++++++++++++++
* minor fixes

0.1.11 (2017-08-28)
+++++++++++++++++++
* revisit of bug 3934 -- policy creation no longer clears existing policies.

0.1.10 (2017-07-27)
+++++++++++++++++++
* fix bug 3934 -- policy creation no longer clears existing policies.

0.1.9 (2017-07-07)
++++++++++++++++++
* minor fixes

0.1.8 (2017-06-21)
++++++++++++++++++
* No changes.

0.1.7 (2017-06-13)
++++++++++++++++++
* Minor fixes.

0.1.6 (2017-05-30)
+++++++++++++++++++++

* Minor fixes.

0.1.5 (2017-05-05)
+++++++++++++++++++++

* Minor fixes.

0.1.4 (2017-04-28)
+++++++++++++++++++++

* New packaging system.

0.1.3 (2017-04-17)
+++++++++++++++++++++

* Apply core changes required for API profile support (#2834) & JSON string parsing from shell (#2705)

0.1.2 (2017-04-03)
+++++++++++++++++++++

* Add note about being in preview (#2512)

0.1.1b3 (2017-02-22)
+++++++++++++++++++++

* Documentation updates.


0.1.1b2 (2017-01-30)
+++++++++++++++++++++

* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* [IoT] update IoT management SDK to 0.2.1
* Add new commands to 'iot hub' and 'iot device' group

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
