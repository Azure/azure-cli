.. :changelog:

Release History
===============

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
