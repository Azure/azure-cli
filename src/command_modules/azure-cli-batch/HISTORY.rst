.. :changelog:

Release History
===============

3.3.3
+++++
* Update Batch Management SDK dependency

3.3.2
+++++
* Update Key Vault SDK dependency

3.3.1
+++++
* Fix bug when show AAD token in cloudshell

3.3.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.
* Fix bug on using token credential on cloud shell mode
* When use json file as input parameter, deserialize content with case insentive.

3.2.6
+++++
* Minor fixes

3.2.5
+++++
* Minor fixes

3.2.4
+++++
* Remove azure-batch-extensions dependency.

3.2.3
+++++
* Fixed bug in Pool list table formatting: issue #4378.

3.2.2
+++++
* Updated to Batch SDK 4.1.2.

3.2.1
+++++
* Minor fixes.

3.2.0
+++++
* Updated to Batch SDK 4.1.1.
* `sdist` is now compatible with wheel 0.31.0

3.1.11
++++++
* Support Autorest 3.0 based SDKs

3.1.10
++++++
* Minor fixes

3.1.9
+++++
* minor fixes

3.1.8
+++++
* Converted to Knack framework
* `az batch login` command now returns authentication details.

3.1.7
+++++
* Fixed bug in pool create command when a resource ID was used with the --image flag.

3.1.6
+++++
* minor fixes

3.1.5 (2017-10-09)
++++++++++++++++++
* Updated to Batch SDK 4.0.0.
* Updated --image option of VirtualMachineConfiguration to support ARM image references in addition to publish:offer:sku:version.
* Now supports the new CLI extension model for Batch Extensions commands - support for old component model has been removed.

3.1.4 (2017-09-22)
++++++++++++++++++
* minor fixes

3.1.3 (2017-09-11)
++++++++++++++++++
* minor fixes

3.1.2 (2017-08-28)
++++++++++++++++++
* minor fixes

3.1.1 (2017-08-11)
++++++++++++++++++

* Updated to Batch SDK 3.1.0 and Batch Management SDK 4.1.0.
* Added a new command show the task counts of a job.
* Fixed bug in resource file SAS URL processing
* Batch account endpoint now supports optional 'https://' prefix.
* Support for adding lists of more than 100 tasks to a job.
* Added debug logging for loading Extensions command module.

3.0.3 (2017-07-07)
++++++++++++++++++
* minor fixes

3.0.2 (2017-06-21)
++++++++++++++++++
* No changes

3.0.1 (2017-06-13)
++++++++++++++++++
* Minor fixes.

3.0.0 (2017-05-30)
++++++++++++++++++

* Updated to Batch SDK 3.0.0 with support for low-priority VMs in pools.
* Changes to the pool create command: --target-dedicated has been renamed to --target-dedicated-nodes and two
  new options have been added; --target-low-priority-nodes and --application-licenses

2.0.4 (2017-05-09)
++++++++++++++++++++

* Minor fixes.

2.0.3 (2017-05-05)
++++++++++++++++++++

* Minor fixes.

2.0.2 (2017-04-28)
++++++++++++++++++++

* New packaging system.

2.0.1 (2017-04-17)
++++++++++++++++++++

* Improve performance of package load and command execution (#2819)
* Apply core changes required for API profile support (#2834) & JSON string parsing from shell (#2705)

2.0.0 (2017-04-03)
++++++++++++++++++++

* Module is GA.
* [Batch] Added output table formatting (#2602)

0.1.1b5 (2017-03-13)
++++++++++++++++++++

* Latest Batch Commands (#2413)
* Load optional command extensions (#2284)


0.1.1b4 (2017-02-22)
++++++++++++++++++++

* Documentation updates.


0.1.1b3 (2017-02-17)
+++++++++++++++++++++

* Add 'azure batch account login' command to enable aad auth
* Add Batch data plane commands
* Prompts for yes / no use the -y option rather than --force


0.1.1b2 (2017-01-30)
+++++++++++++++++++++

* Add path expansion to file type parameters.
* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* Initial preview release.

