.. :changelog:

Release History
===============

2.3.0
+++++
* BREAKING CHANGE: `storage blob/file/container/share list`- Limit default number of results returned to be 5,000.
  Use `--num-results *` for original behavior of returning all results.
* `storage blob/file/container/share list`- log marker for next page to STDERR and expose `--marker` parameter.

2.2.7
+++++
* `storage logging update`- Add ability to update log schema version for storage services.

2.2.6
+++++
* Minor fixes.

2.2.5
+++++
* Improve handling of corner cases for storage copy commands.
* Fix issue with `storage blob copy start-batch` not using login credentials when the destination and source accounts are the same.
* `storage blob/file url`- fix bug with sas_token not being incorporated into url.
* Warn users about future breaking change: `blob/container list` will output first 5000 results by default.

2.2.4
+++++
* Allow connection to storage services only with SAS and endpoints (without an account name or a key) as described in
  `Configure Azure Storage connection strings <https://docs.microsoft.com/azure/storage/common/storage-configure-connection-string>`_.

2.2.3
+++++
* Fix `az storage cors list` output formatting, all items show correct "Service" key
* `--bypass-immutability-policy` parameter for immutability-policy blocked container deletion

2.2.2
+++++
* `--auth-mode login` parameter allows use of user's login credentials for blob and queue authorization.
* Added `storage container immutability-policy/legal-hold` to manage immutable storage.

2.2.1
+++++
* `storage share policy show`: exception handling to exit with code 3 upon a missing resource for consistency.

2.2.0
+++++
* BREAKING CHANGE: `storage account show-usage` now requires `--location` parameter and will list by region.
* Make '--resource-group' parameter optional for 'storage account' commands.
* Remove 'Failed precondition' warnings for individual failures in batch commands for single aggregated message.
* blob/file delete-batch commands no longer output array of nulls.
* blob download/upload/delete-batch commands will read sas-token from container url

2.1.1
+++++
* Allows download of large files using a single connection.
* Converted 'show' commands that were missed from failing with exit code 3 upon a missing resource.

2.1.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.
* Added `pageRanges` property to `storage blob show` output that will be populated for page blobs.

2.0.36
++++++
* Minor fixes

2.0.35
++++++
* Changed table output for `storage blob download` to be more readable.

2.0.34
++++++
* Added extra mimetypes for json and javascript to be inferred from file extensions.

2.0.33
++++++
* Added completer for `--account-name` argument.
* Fixed problem with `storage entity query`.

2.0.32
++++++
* Allow destination sas-token to apply to source for blob copy if source sas and account key are unspecified.
* Expose --socket-timeout for blob uploads and downloads.
* Treat blob names that start with path separators as relative paths.
* `storage blob copy` Allow --source-sas with starting query char, '?'
* `storage entity query` Fix --marker to accept list of key=values.

2.0.31
++++++
* Better error message for malformed connection strings.
* `sdist` is now compatible with wheel 0.31.0

2.0.30
++++++
* Fix issue of upload file with size between 195GB and 200GB

2.0.29
++++++
* Minor fixes.

2.0.28
++++++
* Fix problems with append blob uploads ignoring condition parameters.

2.0.27
++++++
* Fix issue of missing endpoint suffix in batch copy command.
* Blob batch commands no longer throw error upon failed precondition.
* Support Autorest 3.0 based SDKs

2.0.26
++++++
* Enabled specifying destination-path/prefix to blobs in batch upload and copy commands.

2.0.25
++++++
* Added `storage blob service-properties delete-policy` and `storage blob undelete` commands to enable soft-delete.

2.0.24
++++++
* `storage account update`: do not create new networkRuleSet if "default_action" arg is not provided.
* Added progress reporting for all upload/download commands, including batch.
* `storage account check-name`: fixed bug preventing "-n" arg option.
* Added 'snapshot' column to table output for blob list/show.
* Fixed bugs with various parameters that needed to be parsed as ints, added test coverage.
* Small fix with test, `storage blob service-properties show`: "hourMetrics.enabled" defaults to false.

2.0.23
++++++
* Minor fixes.

2.0.22
++++++
* Update for CLI core changes.

2.0.21
++++++
* Update managed storage SDK to 1.5.0
* Support storage v2

2.0.20
++++++
* Update multiapi storage package dependency to 0.1.7

2.0.19
++++++
* `storage account create`: defaults --sku to 'Standard_RAGRS'
* Fixed bugs when dealing with file/blob names that include non-ascii chars.
* `storage blob/file copy start-batch`: Fixed bug that prevented using --source-uri.
* `storage blob/file delete-batch`: Added commands to glob and delete multiple blobs/files.
* `storage metrics update`: fixed bug with enabling metrics.
* `storage blob upload-batch`: Increase block size when target file is over 200GB.
* `storage account create/update`: Fix issue where --bypass and --default-action arguments were ignored.

2.0.18
++++++
* Minor fixes

2.0.17 (2017-10-09)
+++++++++++++++++++
* File share snapshot

2.0.16 (2017-09-22)
+++++++++++++++++++
* `storage account network-rule`: Fixed issue where commands may fail after updating the SDK.

2.0.15 (2017-09-11)
+++++++++++++++++++
* minor fixes

2.0.14 (2017-08-31)
+++++++++++++++++++
* `storage account create`: Fix issue where storage accounts could not be created in regions that don't
  support the NetworkACLs feature.
* Deduce content type and content encoding during blob and file upload if neither content type and content encoding are specified.

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
