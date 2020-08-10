Microsoft Azure SDK for Python
==============================

This is the Microsoft Azure Data Lake Analytics Management Client Library.

Azure Data Lake Analytics Manager (ARM) is the next generation of management APIs that
replace the old Azure Service Management (ASM).

This package has been tested with Python 2.7, 3.3, 3.4 and 3.5.

For the older Azure Service Management (ASM) libraries, see
`azure-servicemanagement-legacy <https://pypi.python.org/pypi/azure-servicemanagement-legacy>`__ library.

For a more complete set of Azure libraries, see the `azure <https://pypi.python.org/pypi/azure>`__ bundle package.


Compatibility
=============

**IMPORTANT**: If you have an earlier version of the azure package
(version < 1.0), you should uninstall it before installing this package.

You can check the version using pip:

.. code:: shell

    pip freeze

If you see azure==0.11.0 (or any version below 1.0), uninstall it first:

.. code:: shell

    pip uninstall azure


Usage
=====

For code examples, see `Data Lake Analytics Management 
<https://azure-sdk-for-python.readthedocs.org/en/latest/sample_azure-mgmt-datalake-analytics.html>`__
on readthedocs.org.


Provide Feedback
================

If you encounter any bugs or have suggestions, please file an issue in the
`Issues <https://github.com/Azure/azure-sdk-for-python/issues>`__
section of the project.


.. :changelog:

Release History
===============
0.2.1 (2019-03-12)
++++++++++++++++++

* Updating permissible versions of the msrestazure package to unblock `Azure/azure-cli#6973 <https://github.com/Azure/azure-cli/issues/6973>`_.

0.2.0 (2017-08-17)
++++++++++++++++++

**Breaking changes**

* Revised the inheritance structure for objects dealing with job creation, building, and retrieving.

  * NOTE: Only U-SQL is supported in this change; therefore, Hive is not supported.
  * When submitting jobs, change JobInformation objects to CreateJobParameters.

    * When setting the properties for the CreateJobParameters object, be sure to change the USqlJobProperties object to a CreateUSqlJobProperties object.

  * When building jobs, change JobInformation objects to BuildJobParameters objects.

    * When setting the properties for the BuildJobParameters object, be sure to change the USqlJobProperties object to a CreateUSqlJobProperties object.
    * NOTE: The following fields are not a part of the BuildJobParameters object:

	  * degreeOfParallelism
	  * priority
	  * related

  * When getting a list of jobs, the object type that is returned is JobInformationBasic and not JobInformation (more information on the difference is below in the Notes section)

* When getting a list of accounts, the object type that is returned is DataLakeAnalyticsAccountBasic and not DataLakeAnalyticsAccount (more information on the difference is below in the Notes section)

**Notes**

* When getting a list of jobs, the job information for each job now includes a strict subset of the job information that is returned when getting a single job

  * The following fields are included in the job information when getting a single job but are not included in the job information when getting a list of jobs:

	* errorMessage
	* stateAuditRecords
	* properties

	  * runtimeVersion
	  * script
	  * type

* When getting a list of accounts, the account information for each account now includes a strict subset of the account information that is returned when getting a single account

  * There are two ways to get a list of accounts: List and ListByResource methods
  * The following fields are included in the account information when getting a list of accounts, which is less than the account information retrieved for a single account:

	* provisioningState
	* state
	* creationTime
	* lastModifiedTime
	* endpoint

* When retrieving account information, an account id field called "accountId" is now included.

  * accountId's description: The unique identifier associated with this Data Lake Analytics account.

0.1.6 (2017-06-19)
++++++++++++++++++
* Fixing a regression discovered in 0.1.5. Please update to 0.1.6 to avoid any issues caused by that regression.

0.1.5 (2017-06-07)
++++++++++++++++++

**New features**

  * Support for Compute Policies on accounts. These will limit specific user and groups to certain job parallelism and priority.
  * Support for job relationship properties. These can be populated in the `related` property when submitting a job and can be retrieved with the `pipeline` and `recurrence` operation methods.
  * Suport for a basic option when listing catalog tables. When set to true, will only return the table name, schema name, database name and version for each table in the list, instead of all table metadata, improving performance when all information is not required.

0.1.4 (2017-04-20)
++++++++++++++++++

**New features**

  * Catalog item get and list support for Packages
  * Update to allow listing certain catalog items from within a database (no schema required to list):

    * list_tables_by_database
    * list_table_valued_functions_by_database
    * list_views_by_database
    * list_table_statistics_by_database
    * list_table_statistics_by_database_and_schema

**Notes**

* This wheel package is now built with the azure wheel extension

0.1.3 (2017-02-13)
++++++++++++++++++

**New features**

* Add support for firewall rules

  * Add, Update, Get, List and Delete operations
  * Enable/Disable the firewall
  *	Allow/Block Azure IPs

*	Remove minimum value requirement from DegreeOfParallelism. If a value <= 0 is passed in, it will be defaulted automatically to 1.
*	Remove unused ErrorDetails object

0.1.2 (2017-01-09)
++++++++++++++++++

**New features**

* Added the ability to create and update accounts with usage commitment levels for Data Lake Store and Data Lake Analytics

**Bugfixes**

* Fixed a bug where three job diagnostic severity types were missing: SevereWarning, UserWarning and Deprecated
* Fixed a bug where UpdateSecret, which is deprecated, was incorrectly indicating that it had a return type. It now properly does not have a return value.

0.1.1 (2016-12-12)
++++++++++++++++++

**New features**

* Add cascade query parameter to DeleteCredential, which allows the user to indicate if they want to delete all resources dependent on the credential as well as the credential
* Parameters are now optional when adding ADLS accounts to an ADLA account
* Fixed a bug in ADLA where the caller could not create an ADLA account with WASB storage accounts.
* Remove invalid return type from Secret creation in ADLA

**Breaking change**

* "account_name" parameter is now "name" in account operation


0.1.0 (2016-11-14)
++++++++++++++++++

* Initial Release


