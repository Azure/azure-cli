.. :changelog:

Release History
===============

2.0.25
++++++
* clarify `--disable-browser` argument
* improve tab completion for --vm-size arguments

2.0.24
++++++
* fix get-credentials command
* aks doesn't need to add role for SPN now

2.0.23
++++++
* Update for CLI core changes.

2.0.22
++++++
* add korea south and korea central to preview regions
* use new flattened managed cluster representation which removes separate "properties" object

2.0.21
++++++
* add `az aks install-connector` and `az aks remove-connector` commands

2.0.20
++++++
* `acs create`: emit out an actionable error if provisioning application failed for lack of permissions
* fix `aks get-credentials -f` without fully-qualified path

2.0.19
++++++
* call "agent" a "node" in AKS to match documentation
* deprecate --orchestrator-release option in acs create
* change default VM size for AKS to Standard_D1_v2
* fix "az aks browse" on Windows
* fix "az aks get-credentials" on Windows

2.0.18
++++++
* fix kubernetes get-credentials

2.0.17 (2017-10-09)
+++++++++++++++++++
* minor fixes

2.0.16 (2017-09-22)
+++++++++++++++++++
* add orchestrator-release option for acs preview regions

2.0.15 (2017-09-11)
+++++++++++++++++++
* add acs list-locations command
* make ssh-key-file come with expected default value

2.0.14 (2017-08-28)
+++++++++++++++++++
* correct preview regions
* format default dns_name_prefix properly
* optimize acs command output

2.0.13 (2017-08-15)
+++++++++++++++++++
* correct sshMaster0 port number for kubernetes

2.0.12 (2017-08-11)
+++++++++++++++++++
* add preview regions

2.0.11 (2017-07-27)
+++++++++++++++++++
* api version 2017-07-01 support
* update dcos and swarm to use latest api version instead of 2016-03-30
* expose orchestrator DockerCE
* fix help message

2.0.10 (2017-07-07)
+++++++++++++++++++
* minor fixes

2.0.9 (2017-06-21)
++++++++++++++++++
* No changes

2.0.8 (2017-06-13)
++++++++++++++++++
* fix acs kube get-credentials ssh-key loading (#3612)
* Change a message so as not to confuse MacOS users. (#3568)
* rbac: clean up role assignments and related AAD application when delete a service principal (#3610)

2.0.7 (2017-05-30)
++++++++++++++++++

* convert master and agent count to integer

2.0.6 (2017-05-09)
++++++++++++++++++

* Minor fixes.

2.0.5 (2017-05-05)
++++++++++++++++++

* Fix to use one of the loaded keys.

2.0.4 (2017-04-28)
++++++++++++++++++

* New packaging system.
* fix the master and agent count to be integer instead of string

2.0.3 (2017-04-17)
++++++++++++++++++

* expose 'az acs create --no-wait' and 'az acs wait' for async creation
* expose 'az acs create --validate' for dry-run validations
* remove windows profile before PUT call for scale command (#2755)

2.0.2 (2017-04-03)
++++++++++++++++++

* Fix kubectl version, always use latest stable. (#2517)
* [ACS] Adding support for configuring a default ACS cluster (#2554)
* [ACS] Provide a short name alias for the orchestrator type flag (#2553)

2.0.1 (2017-03-13)
++++++++++++++++++

* Add support for ssh key password prompting. (#2044)
* Reduce the default number of masters. (#2430)
* Add support for windows clusters. (#2211)
* Switch from Owner to Contributor role. (#2321)
* Remove acs - vm dependency (#2288)
* On scale, clear the service principal profile so that it will update


2.0.0 (2017-02-27)
++++++++++++++++++

* GA release
* Add customizable master_count for Kubernetes cluster create


0.1.2rc2 (2017-02-22)
+++++++++++++++++++++

* Rev compute package to 0.33.rc1 for new API version.
* Documentation fixes.


0.1.2rc1 (2017-02-17)
+++++++++++++++++++++

* Move acs commands from vm to acs module
* Rev kubectl default version
* Show commands return empty string with exit code 0 for 404 responses


0.1.1b3 (2017-02-08)
+++++++++++++++++++++

* Upgrade Azure Management Compute SDK from 0.32.1 to 0.33.0


0.1.1b2 (2017-01-30)
+++++++++++++++++++++

* Generate ssh key file if needed.
* Add help text for get credentials command.
* Add path expansion to file type parameters.
* Fix the double-browser problem with dcos browse.
* Add validation for SSH key format.
* Support Python 3.6.

0.1.1b1 (2017-01-17)
+++++++++++++++++++++

* Detect service principal errors and raise a message.
* Update service principal creation so that it is subscription specific.

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
