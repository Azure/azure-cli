.. :changelog:

Release History
===============

2.0.14
++++++
* Minor fixes

2.0.13
++++++
* `sdist` is now compatible with wheel 0.31.0

2.0.12
++++++
* Performance fixes.

2.0.11
++++++
* Bug fix: Do not require endpoints to be specified when setting --profile for a cloud.

2.0.10
++++++
* `az cloud register` & `az cloud update`: Prevent users from registering clouds that have missing required endpoints

2.0.9
+++++
* minor fixes

2.0.8 (2017-09-22)
++++++++++++++++++
* minor fixes

2.0.7 (2017-07-27)
++++++++++++++++++
* Change api version of cloud metadata endpoint to YYYY-MM-DD format.
* Gallery endpoint isn't required

2.0.6 (2017-07-07)
++++++++++++++++++
* Support for registering cloud just with ARM resource manager endpoint

2.0.5 (2017-06-21)
++++++++++++++++++
* Provide an option for 'az cloud set' to select the profile while selecting current cloud
* Expose 'endpoint_vm_image_alias_doc'

2.0.4 (2017-06-13)
++++++++++++++++++
* Minor fixes.

2.0.3 (2017-05-30)
++++++++++++++++++
* Minor fixes.

2.0.2 (2017-04-28)
++++++++++++++++++
* New packaging system.

2.0.1 (2017-04-17)
++++++++++++++++++
* Add profile switching params and profile listing command
* Modify ‘az cloud register’ and ‘az cloud update’ to include the ‘—profile’ parameter

2.0.0 (2017-02-27)
++++++++++++++++++

* GA release.


0.1.2rc2 (2017-02-22)
+++++++++++++++++++++

* Documentation updates.


0.1.2rc1 (2017-02-17)
+++++++++++++++++++++

* Handle cloud switching in more user friendly way + remove context
* Default to active cloud name and add descriptions for cloud commands


0.1.1b2 (2017-01-30)
+++++++++++++++++++++

* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* Preview release. (no source code changes since previous version).


0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
