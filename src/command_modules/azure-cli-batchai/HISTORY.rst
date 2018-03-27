.. :changelog:

Release History
===============

1.0.0
++++++
* Added support for 2018-03-01 API

 - Job level mounting
 - Environment variables with secret values
 - Performance counters settings
 - Reporting of job specific path segment
 - Support for subfolders in list files api
 - Usage and limits reporting
 - Allow to specify caching type for NFS servers
 - Support for custom images
 - Added pyTorch toolkit support

* Added 'job wait' command which allows to wait for the job completion and reports job exit code
* Added 'usage show' command to list current Batch AI resources usage and limits for different regions
* National clouds are supported
* Added job command line arguments to mount filesystems on the job level in addition to config files
* Added more options to customize clusters - vm priority, subnet, initial nodes count for auto-scale clusters,
  specifying custom image
* Added command line option to specify caching type for Batch AI managed NFS
* Simplified specifying mount filesystem in config files. Now you can omit credentials for Azure File Share and
  Azure Blob Containers - CLI will populate missing credentials using storage account key provided via command line
  parameters or specified via environment variable or will query the key from Azure Storage (if the storage account
  belongs to the current subscription).
* 'job stream-file' now auto-completes when the job is completed (succeeded, failed, terminated or deleted).
* Improved '-o table' support for show operations.

0.1.4
++++++

* Update for CLI core changes.

0.1.3
+++++

* Added short option for providing VM size in file-server create command
* Added storage account name and key arguments into cluster create parameters
* Fixed documentation for job list-files and stream-file
* Added short option for providing cluster name in job create command

0.1.2
+++++
* minor fixes

0.1.1 (2017-10-09)
++++++++++++++++++

* Initial release of Batch AI module.
