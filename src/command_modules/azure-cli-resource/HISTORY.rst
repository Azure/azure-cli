.. :changelog:

Release History
===============
2.0.4 (unreleased)
* Support 'provider operation' commands (#2908)
* Support generic resource create (#2606)

2.0.3 (2017-04-17)
++++++++++++++++++

* Fix resource parsing and api version lookup. (#2781)
* Add docs for az lock update. (#2702)
* Error out if you try to list resources for a group that doesn't exist. (#2769)
* [Compute] Fix issues with VMSS and VM availability set update. (#2773)
* Add some more error checking/handling. (#2768)
* Make argument parameters match up. (#2717)
* Fix lock create and delete if parent-resource-path is None (#2742)
* Apply core changes required for API profile support (#2834) & JSON string parsing from shell (#2705)


2.0.2 (2017-04-03)
++++++++++++++++++

* Add better error messages if --namespace is missing. (#2652)
* Make --parameters repeatable, and merge arguments. (#2656)
* resource: support resource id for generic resource update (#2640)
* Add prompting for missing template parameters. (#2364)

2.0.1 (2017-03-13)
++++++++++++++++++

* Improve docs to point at template deployments command. (#2466)
* core: support setting default values for common arguments like default resource group, default web, default vm (#2414)
* Add some docs for az lock, remove an unused flag, rename another. (#2382)


2.0.0 (2017-02-27)
++++++++++++++++++

* GA release


0.1.2rc2 (2017-02-22)
+++++++++++++++++++++

* Documentation updates.

0.1.2rc1 (2017-02-17)
+++++++++++++++++++++

* Add support for resource links
* Prompts for yes / no use the -y option rather than --force
* Resource delete return the server response
* Show commands return empty string with exit code 0 for 404 responses

0.1.1b2 (2017-01-30)
+++++++++++++++++++++

* Support for management locks.
* Add path expansion to file type parameters.
* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* Add --operation-ids to 'az resource group deployment operations show'.

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
