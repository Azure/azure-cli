.. :changelog:

Release History
===============

2.0.13 (2017-08-28)
+++++++++++++++++++
* Enable set blob tier
* `storage account create/update`: Add `--bypass` and `--default-action` arguments to support service tunneling.
* `storage account network-rule`: Added commands to add VNET rules and IP based rules.
* Enable service encryption by customer managed key
* Breaking change: rename --encryption option to --encryption-services for az storage account create and az storage account update command.
* Fix #4220: az storage account update encryption - syntax mismatch


2.0.12 (2017-08-11)
+++++++++++++++++++
* Enable create storage account with system assigned identity
* Enable update storage account with system assigned identity

2.0.11 (2017-07-27)
+++++++++++++++++++
* Remove --marker option from storage blob list, storage container list, and storage share list commands. The change is a part of the solution to issue #3745. This is technically a breaking change. However since the removed options never works, the impact is limited.
* Enable create https only storage account.

2.0.10 (2017-07-07)
+++++++++++++++++++
* minor fixes

2.0.9 (2017-06-21)
++++++++++++++++++
* No changes.

2.0.8 (2017-06-13)
++++++++++++++++++
* Update storage metrics, logging and cors commands (#3495)
* Fix #3362: Rephrase exception message from CORS add (#3638)
* Fix #3592: convert generator to a list in download batch command dry run mode
* Fix #3592: Blob download batch dryrun issue (#3640)

2.0.7 (2017-05-30)
++++++++++++++++++

* Minor fixes.

2.0.6 (2017-05-09)
++++++++++++++++++

* Minor fixes.

2.0.5 (2017-05-05)
++++++++++++++++++

* Minor fixes.

2.0.4 (2017-04-28)
++++++++++++++++++

* Default location to resource group location for `storage account create`.

2.0.3 (2017-04-17)
++++++++++++++++++

* Add support for incremental blob copy
* Add support for large block blob upload
* Change block size to 100MB when file to upload is larger than 200GB

2.0.2 (2017-04-03)
++++++++++++++++++

* Update storage dependencies (#2654)

2.0.1 (2017-03-02)
++++++++++++++++++
* Fix issue with storage account custom domain setting and updating. (#2346)
* Fix regression in storage copy across accounts

2.0.0 (2017-02-27)
++++++++++++++++++

* GA release.

0.1.2rc2 (2017-02-22)
+++++++++++++++++++++

* Enable copy in same storage account.
* Documentation updates.

0.1.2rc1 (2017-02-17)
+++++++++++++++++++++

* Show commands should return empty string with exit code 0 for 404 responses
* Enable source account name and key in blob copy
* Add generic update capability to storage account create
* Fix #2004: not to query key when sas presents (#2063)
* Prompts for yes / no use the -y option rather than --force
* Address part of #1955 (specifically `az storage entity insert`)
* Ensure container names do not conflict

0.1.1b2 (2017-01-30)
+++++++++++++++++++++

* Provide better error message when missing storage connection info.
* Support UTC datettime with seconds as accepted format. (e.g. 2017-12-31T01:11:59Z).
* Add confirmation prompt for 'storage account delete'.
* Add path expansion to file type parameters.
* Rename storage account keys list parameter.
* Fix #1591: Transform the file and directory list result.
* Fix #1553: Unwrap StorageAccountListKeysResult.
* Fix #1590: Enable listing directories.
* Fix #1561: Retain container permission.
* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* Fix blob type validator.
* Fix copy source convenience parameters.
* Workaround for blob upload.

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
