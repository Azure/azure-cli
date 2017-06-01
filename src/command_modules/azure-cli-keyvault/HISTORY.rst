.. :changelog:

Release History
===============

2.0.5 (2017-05-30)
++++++++++++++++++++

* [Role] Service Principal KeyVault integration (#3133)
* Update KeyVault dataplane to 0.3.2. (#3307)
* [KeyVault] Update data plane SDK to 0.3.0 (#3251)

2.0.3 (2017-05-05)
++++++++++++++++++++

* Minor fixes.

2.0.2 (2017-04-28)
++++++++++++++++++++

* New packaging system.
* BC:`az keyvault certificate download` change -e from string or binary to PEM or DER to better represent the options
* BC: Remove --expires and --not-before from `keyvault certificate create` as these parameters are not supported by the service.
* Adds the --validity parameter to `keyvault certificate create` to selectively override the value in --policy
* Fixes issue in `keyvault certificate get-default-policy` where 'expires' and 'not_before' were exposed but 'validity_in_months' was not.

2.0.1 (2017-04-17)
++++++++++++++++++++

* keyvault fix for import of pem and pfx (#2754)
* Apply core changes required for API profile support (#2834) & JSON string parsing from shell (#2705)

2.0.0 (2017-04-03)
++++++++++++++++++++

* [KeyVault] KeyVault create fix (#2648)
* Fix #2422. (#2514)
* [KeyVault] Command fixes (#2474)
* Fix issue with "single tuple" options_list (#2495)

0.1.1b6 (2017-03-13)
++++++++++++++++++++

* Enable creation of KeyVault using service principal. (#2447)
* Add --secrets for VM and VMSS (#2212)

0.1.1b5 (2017-02-22)
+++++++++++++++++++++

* Documentation updates.


0.1.1b4 (2017-02-17)
+++++++++++++++++++++

* Show commands return empty string with exit code 0 for 404 responses


0.1.1b3 (2017-01-30)
+++++++++++++++++++++

* Add KeyVault file completers.
* Add path expansion to file type parameters.
* Support UTC datettime with seconds as accepted format. (e.g. 2017-12-31T01:11:59Z).
* Support Python 3.6.


0.1.1b2 (2017-01-19)
+++++++++++++++++++++

* Modify telemetry code to be compatible with the change to azure-cli-core 0.1.1b2.


0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* Remove embedded KeyVault client and use KeyVault SDK.

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
