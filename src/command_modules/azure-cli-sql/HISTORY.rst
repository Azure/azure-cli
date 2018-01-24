.. :changelog:

Release History
===============

2.0.20
++++++
* Clean up unused test files

2.0.19
++++++
* Updated helpfile

2.0.18
++++++
* Update for CLI core changes.

2.0.17
++++++
* Update managed storage SDK dependency

2.0.16
++++++
* Added az sql db list-usages and az sql db show-usage commands.
* Added sql server conn-policy show/update commands.

2.0.15
++++++
* Added --ignore-missing-vnet-service-endpoint param to az sql server vnet-rule create and update commands
* Minor fixes.

2.0.14
++++++
* Minor fixes

2.0.13 (2017-10-09)
+++++++++++++++++++
* Adding support for SQL Transparent Data Encryption (TDE) and TDE with Bring Your Own Key
* Added az sql db list-deleted command and az sql db restore --deleted-time parameter, allowing the ability to find and restore deleted databases.
* Added az sql db op list and az sql db op cancel, allowing the ability to list and cancel in-progress operations on database.

2.0.12 (2017-09-22)
+++++++++++++++++++
* az sql server list --resource-group argument is now optional. If not specified, all sql servers in the entire subscription will be returned.
* Added --no-wait param to db create, db copy, db restore, db update, db replica create, dw create, and dw update commands

2.0.11 (2017-09-11)
+++++++++++++++++++
* Added az sql server vnet-rule commands.

2.0.10 (2017-08-28)
+++++++++++++++++++
* minor fixes

2.0.9 (2017-08-11)
++++++++++++++++++
* minor fixes

2.0.8 (2017-07-27)
++++++++++++++++++
* minor fixes

2.0.7 (2017-07-07)
++++++++++++++++++

* Removed broken az sql server create --identity parameter.

2.0.6 (2017-06-21)
++++++++++++++++++

* az sql server create/update command output no longer show administratorLoginPassword values.

2.0.5 (2017-06-13)
++++++++++++++++++

* Added az sql db list-editions and az sql elastic-pool list-editions commands.

2.0.4 (2017-05-30)
++++++++++++++++++

* Minor fixes.

2.0.3 (2017-05-09)
++++++++++++++++++

* Minor fixes.

2.0.2 (2017-04-28)
++++++++++++++++++

* Added az sql server list-usages and az sql db list-usages commands.

2.0.1 (2017-04-17)
++++++++++++++++++

* SQL - ability to connect directly to resource provider (#2832)
* Fix doc references to azure.cli.commands (#2740)
* Apply core changes required for API profile support (#2834) & JSON string parsing from shell (#2705)

2.0.0 (2017-04-03)
++++++++++++++++++

* Removed duplicate sql utils code (#2629)
* Import/Export CLI changes for SAS key (#2584)
* SQL database audit and threat detection commands (#2536)
* Sql Import/Export CLI commands and test (#2538)
* Require confirmation for destructive SQL commands. (#2509)

0.1.1b6 (2017-03-13)
++++++++++++++++++++

* Design changes and tests for SQL DB replication commands (#2379)
* Design tweaks and functional test for SQL db restore command (#2423)
* Implemented and tested SQL Data Warehouse commands (#2351)
* Removed service-objective commands. (#2380)
* SQL core commands (server, db, and elastic pool) (#2253)

0.1.1b5 (2017-02-27)
++++++++++++++++++++

* Parameter help fix.

0.1.1b4 (2017-02-22)
++++++++++++++++++++

* Documentation updates.

0.1.1b3 (2017-01-30)
++++++++++++++++++++

* Fix SQL command aliases.
* Support Python 3.6.

0.1.1b2 (2017-01-19)
++++++++++++++++++++

* Fix incorrect sql parameter register
* Expanding ElasticPool while creating elastic-pool
* Fix incorrect type of subgroup in help

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* Add Azure SQL Server commands.

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
