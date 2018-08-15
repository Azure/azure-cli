.. :changelog:

Release History
===============

0.1.1
+++++
* Minor fixes

0.1.0
++++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.

0.0.23
++++++
* Minor fixes.

0.0.22
++++++
* Minor fixes.

0.0.21
++++++
* `sdist` is now compatible with wheel 0.31.0

0.0.20
++++++
* Updated the ADLS version to latest.

0.0.19
++++++
* Update for CLI core changes.

0.0.18
++++++
* Change the return type of the account list command: a list of DataLakeStoreAccount to a list of DataLakeStoreAccountBasic
* The properties of a Basic type is a strict subset of the properties of a regular type

0.0.17
++++++
* Minor fixes.

0.0.16
++++++
* minor fixes

0.0.15 (2017-10-09)
+++++++++++++++++++
* minor fixes

0.0.14 (2017-09-22)
+++++++++++++++++++
* minor fixes

0.0.13 (2017-08-28)
+++++++++++++++++++
* minor fixes

0.0.12 (2017-08-11)
+++++++++++++++++++
* Enable progress controller (#4072)


0.0.11 (2017-07-27)
+++++++++++++++++++
* Allow finer grained chunking for Data Lake Store transfer (#4014)

0.0.10 (2017-07-07)
+++++++++++++++++++
* Add support for user managed key vault key rotation in `dls account update`

0.0.9 (2017-06-21)
++++++++++++++++++
* No changes.

0.0.8 (2017-06-13)
++++++++++++++++++
* Minor fixes.

0.0.7 (2017-05-30)
++++++++++++++++++

* Update underlying Data Lake Store filesystem SDK version, addressing a performance issue.
* Update to add a new command: `az dls enable-key-vault`. This command attempts to enable a user provided Key Vault for use encrypting the data in a Data Lake Store account.

0.0.6 (2017-05-09)
++++++++++++++++++

* Minor fixes.

0.0.5 (2017-05-05)
++++++++++++++++++

* Minor fixes.

0.0.4 (2017-05-01)
++++++++++++++++++

* Update the version of the underlying filesystem SDK, which gives better support for handling server side throttling scenarios.

0.0.3 (2017-04-28)
++++++++++++++++++

* New packaging system.

0.0.2 (2017-04-17)
++++++++++++++++++

* Improve performance of package load and command execution (#2819)
* missed help for access show. adding it. (#2743)
* Apply core changes required for API profile support (#2834) & JSON string parsing from shell (#2705)

0.0.1 (2017-04-03)
++++++++++++++++++

* Initial release of dls (Data Lake Store) package based on the removed datalake store commands.
* add ACL management commands
* rename file subgroup to fs
* move all permissions commands under 'access' sub group under fs
* add file expiry command
