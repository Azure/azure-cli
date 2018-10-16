.. :changelog:

Release History
===============

0.1.1
+++++
* Update azure-mgmt-devtestlabs dependency to 2.2.0

0.1.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.

0.0.23
++++++
* Minor fixes.

0.0.22
++++++
* Fix regression from knack conversion that replaced table_transformers with transforms.

0.0.21
++++++
* `sdist` is now compatible with wheel 0.31.0

0.0.20
++++++
* Fixed create enviorment.

0.0.19
++++++
* Minor fixes.

0.0.18
++++++
* Minor fixes.

0.0.17
++++++
* Minor fixes.

0.0.16
++++++
* Performance fixes.

0.0.15
++++++
* Update helpfile

0.0.14
++++++
* Update for CLI core changes.

0.0.13
++++++
* Minor fixes.

0.0.12
++++++
* minor fixes

0.0.11 (2017-09-22)
+++++++++++++++++++
* minor fixes

0.0.10 (2017-08-28)
+++++++++++++++++++
* minor fixes

0.0.9 (2017-07-27)
++++++++++++++++++
* minor fixes

0.0.8 (2017-07-07)
++++++++++++++++++
* minor fixes

0.0.7 (2017-06-21)
++++++++++++++++++
* No changes.

0.0.6 (2017-06-13)
++++++++++++++++++
* Minor fixes.

0.0.5 (2017-05-30)
+++++++++++++++++++++

* Adding support for claiming any vm in the lab through `az lab vm claim`
* Adding support for claiming existing vm in the lab through `az lab vm claim`
* Adding table output formatter for `az lab vm list` & `az lab vm show`

0.0.4 (2017-05-05)
+++++++++++++++++++++

* Adding table output formatter for az lab arm-template & az lab artifact-source

0.0.3 (2017-04-28)
+++++++++++++++++++++

* Adding create, show, delete & list commands for environment in the lab.
* Adding show & list commands to view ARM templates in the lab.
* Adding --environment flag in `az lab vm list` to filter VMs by environment in the lab.

0.0.2 (2017-04-17)
+++++++++++++++++++++

* Add convenience command `az lab formula export-artifacts` to export artifact scaffold within a Lab's formula.
* Add commands to manage secrets within a Lab.

0.0.1 (2017-04-03)
+++++++++++++++++++++

* Preview release.
