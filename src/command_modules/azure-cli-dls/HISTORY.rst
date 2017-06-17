.. :changelog:

Release History
===============
0.0.8 (2017-06-13)
^^^^^^^^^^^^^^^^^^
* Remove useless line-too-long suppression
* Fix all bad-continuation pylint disables
* Fix various pylint disable rules
* Fix all superflusous-parens pylint disable rules
* Fix method-hidden pylint disable rule
* Move all existing recording files to latest folder

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
