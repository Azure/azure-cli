.. :changelog:

Release History
===============
2.0.25
++++++
Minor fix

2.0.24
++++++
* Add ACR Build commands.
* Improve resource not found error messages.
* Improve resource creation performance and error handling.
* Improve acr login in non-standard consoles and WSL.
* Improve repository commands error messages.
* Update table columns and ordering.

2.0.23
++++++
* Improve error handling of wincred fallback.
* `sdist` is now compatible with wheel 0.31.0

2.0.22
++++++
* Improve repository delete command with --image parameter to support docker image format.
* Deprecate --manifest and --tag parameters in repository delete command.
* Add acr repository untag command to remove a tag without deleting data.

2.0.21
++++++
* Minor fixes

2.0.20
++++++
* minor fix

2.0.19
++++++
* Add acr login fallback on wincred errors.
* Minor fixes, enable registry logs.

2.0.18
++++++
* Update for CLI core changes.

2.0.17
++++++
* Update managed storage SDK dependency

2.0.16
++++++
* Documentation fixes.

2.0.15
++++++
* Add creating webhooks in replication regions.

2.0.14
++++++
* All resource management now points to 2017-10-01 api-version.
* Bring your own storage SKU is now Classic.
* Managed registry SKUs are now Basic, Standard, and Premium.

2.0.13 (2017-10-09)
+++++++++++++++++++
* minor fixes

2.0.12 (2017-09-22)
+++++++++++++++++++
* minor fixes

2.0.11 (2017-08-28)
+++++++++++++++++++
* minor fixes

2.0.10 (2017-08-11)
+++++++++++++++++++
* minor fixes

2.0.9 (2017-07-27)
++++++++++++++++++
* Add show-usage command for managed registries.
* Support SKU update for managed registries.

2.0.8 (2017-07-07)
++++++++++++++++++
* minor fixes

2.0.7 (2017-06-21)
++++++++++++++++++
* Add managed registries with Managed SKU.
* Add webhooks for managed registries with acr webhook command module.
* Add AAD authentication with acr login command.
* Add delete command for docker repositories, manifests, and tags.

2.0.6 (2017-06-13)
++++++++++++++++++
* Minor fixes.

2.0.5 (2017-05-30)
++++++++++++++++++

* Minor fixes.

2.0.4 (2017-05-09)
++++++++++++++++++

* Minor fixes.

2.0.3 (2017-05-05)
++++++++++++++++++

* Minor fixes.

2.0.2 (2017-04-28)
++++++++++++++++++

* New packaging system.

2.0.1 (2017-04-17)
++++++++++++++++++

* Apply core changes required for API profile support (#2834) & JSON string parsing from shell (#2705)

2.0.0 (2017-04-03)
++++++++++++++++++

* Module is GA.
* [ACR] Update to 2017-03-01 api-version (#2563)

0.1.1b5 (2017-03-13)
++++++++++++++++++++

* --admin-enabled no longer requires an input value

0.1.1b4 (2017-02-22)
++++++++++++++++++++

* Documentation fixes.


0.1.1b3 (2017-02-17)
++++++++++++++++++++

* Polish error messages for repository/credential commands
* Storage account sku validation
* Show commands return empty string with exit code 0 for 404 responses


0.1.1b2 (2017-01-30)
++++++++++++++++++++

* Support Python 3.6.
* Fix storage account name with capital letters.


0.1.1b1 (2017-01-17)
++++++++++++++++++++

* Update ACR SDK version to 0.1.1
* Add tty check before prompting for user input
* Enable storage account encryption by default


0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
