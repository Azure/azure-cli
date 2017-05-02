.. :changelog:

Release History
===============
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

