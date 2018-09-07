.. :changelog:

Release History
===============

0.3.3
+++++
* Add '--secure-environment-variables' for passing secure environment variables to a container

0.3.2
+++++
* Do not require '--log-analytics-workspace-key' for name or ID when in set subscription

0.3.1
+++++
* Update PyYAML dependency to 3.13

0.3.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.
* Remove the requirement for username and password for non dockerhub registries
* Fix error when creating container groups from yaml file

0.2.1
+++++
* Update PyYAML dependency to 4.2b4

0.2.0
+++++
* Default to long running operation for `az container create`
* Add Log Analytics parameters '--log-analytics-workspace' and '--log-analytics-workspace-key'
* Add --protocol parameter to specify which network protocol to use

0.1.24
++++++
* Allow exporting a container group in yaml format.
* Allow using a yaml file to create / update a container group.

0.1.23
++++++
* Do not require --registry-server for `az container create` when a registry server is included in the image name.

0.1.22
++++++
* Add Git Repo volume mount parameters '--gitrepo-url' '--gitrepo-dir' '--gitrepo-revision' and '--gitrepo-mount-path'

0.1.21
++++++
* Fixed [#5926](https://github.com/Azure/azure-cli/issues/5926): Fix `az container exec` failing when --container-name specified
* `sdist` is now compatible with wheel 0.31.0

0.1.20
++++++
* Add 'az container exec' command that allows for exec commands in a container for a running container group.
* Allow table output for creating and updating a container group.

0.1.19
++++++
* Add '--secrets' and '--secrets-mount-path' options to 'az container create' for using secrets in ACI

0.1.18
++++++
* Add '--follow' option to 'az container logs' for streaming logs
* Add 'az container attach' command that attaches local standard output and error streams to a container in a container group.

0.1.17
++++++
* Minor fixes

0.1.16
++++++
* Update for CLI core changes.

0.1.15
++++++
* Fix incorrect order of parameters for container logs

0.1.14
++++++
* Fixed default ports regression

0.1.13
++++++
* minor fixes
* Added support to open multiple ports
* Added container group restart policy
* Added support to mount Azure File share as a volume
* Updated helper docs

0.1.12
++++++
* minor fixes

0.1.11 (2017-09-22)
+++++++++++++++++++
* minor fixes

0.1.10 (2017-09-11)
+++++++++++++++++++
* minor fixes

0.1.9 (2017-08-28)
++++++++++++++++++
* minor fixes

0.1.8 (2017-08-11)
++++++++++++++++++

* container create: Fixes issue where equals sign was not allowed inside an environment variable.


0.1.7 (2017-07-27)
++++++++++++++++++

* Preview release.
