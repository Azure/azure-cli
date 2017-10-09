.. :changelog:

Release History
===============
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
* minor fixes

2.0.8 (2017-07-07)
++++++++++++++++++
create-for-rbac: support output in SDK auth file format

2.0.7 (2017-06-21)
++++++++++++++++++
* No changes.

2.0.6 (2017-06-13)
++++++++++++++++++
* rbac: clean up role assignments and related AAD application when delete a service principal (#3610)

2.0.5 (2017-05-30)
++++++++++++++++++
* ad: for 'app create' command, mention time format in the arg descriptions for --start-date/--end-date
* output deprecating information on using '--expanded-view'
* Add Key Vault integration to the create-for-rbac and reset-credentials commands.


2.0.4 (2017-05-09)
++++++++++++++++++
* Minor fixes.

2.0.3 (2017-04-28)
++++++++++++++++++
* create-for-rbac: ensure SP's end date will not exceed certificate's expiration date (#2989)
* RBAC: add full support for 'ad group' (#2016)

2.0.2 (2017-04-17)
++++++++++++++++++
* role: fix issues on role definition update (#2745)
* create-for-rbac: ensure user provided password is picked up

2.0.1 (2017-04-03)
++++++++++++++++++

* role: fix the error when supply role in guid format (#2667)
* Fix code style of azure-cli-role (#2608)
* rbac:catch more graph error (#2567)
* core: support login using service principal with a cert (#2457)

2.0.0 (2017-02-27)
++++++++++++++++++

* GA release.


0.1.2rc2 (2017-02-22)
+++++++++++++++++++++

* Documentation updates.


0.1.2rc1 (2017-02-17)
+++++++++++++++++++++

* Support --skip-assignment for 'az ad sp create-for-rbac'
* Show commands return empty string with exit code 0 for 404 responses


0.1.1b2 (2017-01-30)
+++++++++++++++++++++

* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* 'create-for-rbac' command accepts displayname.

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
