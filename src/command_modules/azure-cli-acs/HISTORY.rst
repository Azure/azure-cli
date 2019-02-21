.. :changelog:

Release History
===============

* add listen-address option to "az aks port-forward"

2.3.17
++++++
* az aks enable-addons /disable-addons: support case insensitive name
* support Azure Active Directory updating operation using "az aks update-credentials --reset-aad"
* clarify that "--output" is ignored for "az aks get-credentials"

2.3.16
++++++
* Minor fixes

2.3.15
++++++
* Add Virtual Nodes Preview
* Add Managed OpenShift commands
* Support Service Principal updating operation using "az aks update-credentials --reset-service-principal"

2.3.14
++++++
* Minor fixes
* Add support for new ACI regions

2.3.13
++++++
* Add Virtual Nodes Preview
* Remove "(PREVIEW)" from AAD arguments to "az aks create"
* Mark "az acs" commands as deprecated (the ACS service will retire on January 31, 2020)
* Add support of Network Policy when creating new AKS clusters
* Don't require --nodepool-name in "az aks scale" if there's only one nodepool

2.3.12
++++++
* Minor fixes

2.3.11
++++++
* BREAKING CHANGE: Remove enable_cloud_console_aks_browse to enable 'az aks browse' by default

2.3.10
++++++
* Minor fixes

2.3.9
+++++
* Minor fixes

2.3.8
+++++
* Minor fixes.

2.3.7
+++++
* Minor fixes.

2.3.6
+++++
* `az aks create/scale --nodepool-name` configures nodepool name, truncated to 12 characters, default - nodepool1

2.3.5
+++++
* bugfix: Fall back to 'scp' when Parimiko fails.
* `az aks create` no longer requires --aad-tenant-id
* bugfix: improve merging of kubernetes credentials when duplicate entries are present.
* In Azure Cloud Shell, open a tunnel and report the URL

2.3.4
+++++
* install-connector: Updates the install-connector command to set the AKS Master FQDN

2.3.3
+++++
* bugfix: creating role assignment for vnet-subnet-id when not specifying service principal and skip-role-assignemnt

2.3.2
+++++
* `az aks create` now defaults to Standard_DS2_v2 VMs.

2.3.1
+++++
* `az aks get-credentials` will now call new apis to get cluster credential.

2.3.0
+++++
* `az acs/aks install-cli` will install to under %USERPROFILE%\.azure-kubectl on Windows
* `az aks install-connector` will now detect if the cluster has RBAC and configure ACI Connector appropriately
* Create role assignment to the subnet when it's provided.
* Add new option "skip role assignment" for subnet when it's provided
* Skip role assignment to subnet when assignment already exists

2.2.2
+++++
* Return 0 (success) when ending `az aks browse` by pressing [Ctrl+C]
* changes for consuming multi api azure.mgmt.authorization package

2.2.1
+++++
* Depdendency update: paramiko >= 2.0.8

2.2.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.
* `az aks create` will error out if `--max-pods` is less than 5

2.1.3
+++++
* Update PyYAML dependency to 4.2b4
* Handle monitoring solution through its subscription ID

2.1.2
+++++
* Breaking change: Enable Kubernetes role-based access control by default.
* Add a `--disable-rbac` argument and deprecate `--enable-rbac` since it's the default now.
* Updated options for `az aks browse` command. Added `--listen-port` support.
* Update the default helm chart package for `az aks install-connector` command. Use virtual-kubelet-for-aks-latest.tgz.
* added `az aks enable-addons` and `disable-addons` commands to update an existing cluster

2.1.1
+++++
* Updated options of `az aks use-dev-spaces` command. Added `--update` support.
* `az aks get-credentials --admin` won't replace the user context in $HOME/.kube/config
* expose read-only "nodeResourceGroup" property on managed clusters
* fix `az acs browse` command error

2.1.0
+++++
* `az aks create` understands advanced networking (VNet) options
* `az aks create` accepts options to enable Log Analytics monitoring and HTTP application routing addons
* `az aks create --no-ssh-key` creates a cluster without using local SSH keys
* `az aks create --enable-rbac` creates a cluster with Kubernetes Role-Based Access Control
* `az aks create` handles Azure Active Directory auth options (PREVIEW)

2.0.34
++++++
* `az aks get-credentials` creates the kube config file with more secure filesystem permissions
* make --connector-name optional for `aks install-connector`, `aks upgrade-connector` and `aks remove-connector`
* add 2 new Azure Container Instance regions for `aks install-connector`
* `aks install-connector` add the normalized location into the helm release name and node name

2.0.33
++++++
* add new Dev-Spaces commands: `az aks use-dev-spaces` and `az aks remove-dev-spaces`
* fix typo in help message

2.0.32
++++++
* remind the user that `az aks` is a preview service
* fix the permission issue in `aks install-connector` when --aci-resource-group is not specified

2.0.31
++++++
* `sdist` is now compatible with wheel 0.31.0

2.0.30
++++++
* Minor fixes
* aks created spn will be valid for 5 years

2.0.29
++++++
* fix a certificate verification error for `az aks install-cli` in Cloud Shell / PS

2.0.28
++++++
* Support Autorest 3.0 based SDKs
* warn the user that `az aks browse` won't work in Azure Cloud Shell
* add `aks upgrade-connector` command to upgrade an existing connector
* `kubectl` config files are more readable block-style YAML

2.0.27
++++++
* use the virtual-kubelet-for-aks helm chart for `aks install-connector` by default
* fix the service principal insufficient permission to create ACI container group issue
* add --aci-container-group, --location, --image-tag optional parameters for `aks install-connector`
* remove deprecation notice from `aks get-versions`

2.0.26
++++++
* rename `aks get-versions` to `aks get-upgrades` in the interest of accuracy
* reimplement `aks get-versions` to show Kubernetes versions available for `aks create`
* `aks create` defaults to letting the server choose the version of Kubernetes
* update help messages referring to the service principal generated by AKS
* `aks create` VM node size default changed from "Standard_D1_v2" to "Standard_DS1_v2"
* improve reliability when locating the dashboard pod for `az aks browse`
* `aks get-credentials` handles UnicodeDecodeError when loading Kubernetes configuration files
* add a message to `az aks install-cli` to help get `kubectl.exe` in the search PATH

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
