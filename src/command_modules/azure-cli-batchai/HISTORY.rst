.. :changelog:

Release History
===============

0.4.2
+++++
* Minor fixes

0.4.1
+++++
* Logger output for auto-storage account creation now specifies "resource *group*".

0.4.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.
* Fixed `az batchai job exec` command

0.3.2
+++++
* Minor fixes

0.3.1
+++++
* Fixed `-o table` option for `az batchai cluster node list` and `az batchai job node list` commands.

0.3.0
+++++
* Added support for 2018-05-01 API

 - Added support for workspaces. Workspaces allow to group clusters, file-servers and experiments in groups removing
   limitation on number of resources can be created;
 - Added support for experiments. Experiments allow to group jobs in collections removing limitation on number of
   created jobs;
 - It's possible to configure /dev/shm for jobs running in docker container.

* Added 'az batchai cluster node exec' and 'az batchai job node exec' commands. These commands allow to execute any
  commands directly on nodes and provide functionality for port forwarding. Port forwarding can be used, for example,
  to access tensorboard and jupyter running on cluster's nodes;
* az batchai now supports --ids parameters like other az commands;
* Breaking change: now all clusters and fileservers must be created under workspaces;
* Breaking change: now jobs must be created under experiments;
* Breaking change: '--nfs-resource-group' option is deleted from 'cluster create' and 'job create' commands. To mount
  NFS belonging to a different workspace/resource group provide file server's ARM ID via '--nfs' option;
* Breaking change: '--cluster-resource-group' option is deleted from 'job create' command. To submit a job on a cluster
  belonging to a different workspace/resource group provide cluster's ARM ID via '--cluster' option;
* Breaking change: jobs, cluster and file servers do not longer have location attribute. Location now is an attribute of
  a workspace. So, '--location' parameter has been removed from 'job create', 'cluster create' and 'file-server create'
  commands;
* Breaking change: names of short options were changed to make interface more consistent:

 - In create cluster, file-server and job commands ['--config', '-c'] option was renamed to ['--config-file', '-f'];
 - In create job command ['--cluster', '-r'] option was renamed to ['--cluster', '-c'];
 - In 'job file list' and 'job file stream' commands ['--job', '-n'] option was renamed to ['--job', '-j'];
 - In 'cluster file list' command ['--cluster', '-n'] option was renamed to ['--cluster', '-c']

0.2.3
+++++
* minor changes

0.2.2
+++++
* Now 'az batchai create cluster' respects vm priority configured in the cluster's configuration file.

0.2.1
+++++
* Minor fixes

0.2.0
+++++
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
* Job file stream command now auto-completes when the job is completed (succeeded, failed, terminated or deleted).
* Improved '-o table' support for show operations.
* Added --use-auto-storage option for cluster creation. This option make it simpler to manage storage accounts and
  and mount Azure File Share and Azure Blob Containers to clusters.
* Added --generate-ssh-keys option into 'cluster create' and 'file-server create'.
* Added ability to provide node setup task via command line.
* Breaking change: 'job stream-file' and 'job list-files' commands are grouped under 'job file' group.
* Breaking change: renamed --admin-user-name to --user-name in 'file-server create' command to be consistent with
  'cluster create' command.

* `sdist` is now compatible with wheel 0.31.0

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
