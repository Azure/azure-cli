.. :changelog:

Release History
===============

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
