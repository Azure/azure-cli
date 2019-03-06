.. :changelog:

Release History
===============

0.2.8
+++++
* Introduce `network-rule` subgroup with commands `add`, `remove`, and `list` for managing VNET rules of a Cosmos DB account

0.2.7
+++++
* Added support for creating database with shared throughput

0.2.6 
+++++ 
* Added support for updating account from multi-master to single-master

0.2.5
+++++
* Use latest azure-mgmt-cosmosdb pypi package (0.5.2)

0.2.4
+++++
* Minor fixes.

0.2.3
+++++
* Minor fixes.

0.2.2
+++++
* `cosmosdb create`: Add `--enable-multiple-write-locations` support.

0.2.1
+++++
* Minor fixes

0.2.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.

0.1.22
++++++
* Minor fixes.

0.1.21
++++++
* Introducing VNET support for Azure CLI - Cosmos DB

0.1.20
++++++
* Minor fixes
* `sdist` is now compatible with wheel 0.31.0

0.1.19
++++++
* Added support for setting capabilities and minor fixes.

0.1.18
++++++
* Minor fixes

0.1.17
++++++
* Fix parameter description for failover policies.

0.1.16
++++++
* Update for CLI core changes.

0.1.15
++++++
* Use latest azure-mgmt-cosmosdb pypi package (0.2.1)

0.1.14
++++++
* minor fixes

0.1.13 (2017-09-22)
+++++++++++++++++++
* minor fixes

0.1.12 (2017-08-28)
+++++++++++++++++++
* minor fixes

0.1.11 (2017-07-27)
+++++++++++++++++++
* Minor fix allowing Creation of Collection with custom partition key

0.1.10 (2017-07-07)
+++++++++++++++++++
* minor fixes

0.1.9 (2017-06-21)
++++++++++++++++++

* Added Support for Collection Default TTL.

0.1.8 (2017-06-13)
++++++++++++++++++
* Minor fixes.

0.1.7 (2017-05-30)
++++++++++++++++++
* Minor fixes.

0.1.6 (2017-05-09)
++++++++++++++++++

* Rename documentdb module to cosmosdb.

0.1.5 (2017-05-05)
++++++++++++++++++

* Added support for documentdb data-plane APIs:
  database and collection management
* Added support for enabling automatic failover on database accounts
* Added support for new consistency policy ConsistentPrefix
* Upgraded pypi package dependency for azure-mgmt-documentdb to 0.1.3

0.1.4 (2017-04-28)
++++++++++++++++++

* New packaging system.

0.1.3 (2017-04-17)
++++++++++++++++++

* Apply core changes required for API profile support (#2834)

0.1.2 (2017-04-03)
++++++++++++++++++

* DocumentDB: Adding support for listing connection strings (#2580)
* Fix TypeErrors in DocDB (#2566)

0.1.1b2 (2017-02-22)
+++++++++++++++++++++

* Documentation updates.


0.1.1b1 (2017-02-17)
+++++++++++++++++++++

* Initial release.

