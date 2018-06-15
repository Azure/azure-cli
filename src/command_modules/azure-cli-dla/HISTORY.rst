.. :changelog:

Release History
===============

0.1.0
+++++
* Minor fixes.

0.0.19
++++++
* `sdist` is now compatible with wheel 0.31.0

0.0.18
++++++
* Performance fixes.

0.0.17
++++++
* Update helpfile
  
0.0.16
++++++
* Update for CLI core changes.

0.0.15
++++++
* Change the return type of the job list command: a list of JobInformation to a list of JobInformationBasic
* Change the return type of the account list command: a list of DataLakeAnalyticsAccount to a list of DataLakeAnalyticsAccountBasic
* The properties of a Basic type is a strict subset of the properties of a regular type

0.0.14
++++++
* Minor fixes.

0.0.13
++++++
* minor fixes

0.0.12 (2017-09-22)
+++++++++++++++++++
* minor fixes

0.0.11 (2017-08-28)
+++++++++++++++++++
* minor fixes

0.0.10 (2017-07-07)
+++++++++++++++++++
* Add commands for compute policy management under the `dla account compute-policy` heading
* Add show and list commands for job pipeline and recurrence under `dla job pipeline` and `dla job recurrence` respectively


0.0.9 (2017-06-21)
++++++++++++++++++
* No changes.

0.0.8 (2017-06-13)
++++++++++++++++++
* Minor fixes.

0.0.7 (2017-05-30)
++++++++++++++++++

* Minor fixes.

0.0.6 (2017-05-09)
++++++++++++++++++

* Minor fixes.

0.0.5 (2017-05-05)
++++++++++++++++++

* Fix a bug where filtering on result and state for job lists would throw an error.

0.0.4 (2017-05-01)
++++++++++++++++++

* Add support for new catalog item type: package. accessed through: `az dla catalog package`
* Made it possible to list the following catalog items from within a database (no schema specification required):

  * Table
  * Table valued function
  * View
  * Table Statistics. This can also be listed with a schema, but without specifying a table name.

0.0.3 (2017-04-28)
++++++++++++++++++

* New packaging system.

0.0.2 (2017-04-17)
++++++++++++++++++

* Minor text fixes (#2776)
* Apply core changes required for API profile support (#2834) & JSON string parsing from shell (#2705)

0.0.1 (2017-04-03)
++++++++++++++++++

* Initial release of dla (Data Lake Analytics) package based on the removed datalake store commands.
* rename parameters for some catalog management sub groups
* Fix support for the job list command to allow better filtering and ordering

