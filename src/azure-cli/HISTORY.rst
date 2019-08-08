.. :changelog:

Release History
===============

2.0.71
++++++

**AppService**

* az webapp webjob continuous group commands were failing for slots

**BotService**

* BREAKING CHANGE:
    create:
        - Removed support for creating v3 SDK bots
        - Remove `az bot publish` example when creating a Web App bot

**CognitiveServices**

* Add "cognitiveservices account network-rule" commands.

**Cosmos DB**

* Remove warning when updating multiple write locations
* Add CRUD commands for CosmosDB SQL, MongoDB, Cassandra, Gremlin and Table resources and resource's throughput.

**HDInsight**

* BREAKING CHANGE:
    create:
        - Renamed --storage-default-container to --storage-container and --storage-default-filesystem to --storage-filesystem
    application create: 
        - Changed the --name/-n argument to represent the application name instead of the cluster name and added a separate --cluster-name argument
        - Renamed --application-type to --type/-t
        - Renamed --marketplace-identifier to --marketplace-id
        - Renamed --https-endpoint-access-mode to --access-mode and --https-endpoint-destination-port to --destination-port
        - Removed --https-endpoint-location, --https-endpoint-public-port, --ssh-endpoint-destination-port, --ssh-endpoint-location and --ssh-endpoint-public-port
    resize:
        - Renamed --target-instance-count to --workernode-count/-c
    script-action
        - Changed --name/-n to represent the name of the script action and added the --cluster-name argument to represent the cluster name
        - Changed --script-execution-id to --execution-id
        - Renamed the "show" command to "show-execution-details"
    script-action execute:
        - Made parameters for the --roles argument space separated instead of comma separated
    script-action list:
        - Removed the --persisted parameter
* create:
    Enabled the --cluster-configurations argument to accept a path to a local JSON file or a JSON string as the parameter
* script-action list-execution-history:
    Added this command to list the execution history for all script action executions
* monitor enable:
    Enabled the --workspace argument to accept a Log Analytics workspace ID or workspace name as the parameter
    Added the --primary-key argument, which is needed if a workspace ID is provided as the parameter 
* Added more examples and updated descriptions for help messages

**interactive**

* Fix a loading error on 2.0.70

**Network**

* az network dns record-set cname delete: Fixes #10166. Support `--yes` argument to align the behavior with other dns type. 

**Profile**

* Add get-access-token --resource-type enum for convenience of getting access tokens for well-known resources.

**ServiceFabric**

* Fix for issue #6112 - added all supported os version for sf cluster create
* Fix for issue #6536 - primary certificate validation bug

**Storage**

* `storage copy`: add copy command for storage

**Kubernetes**

* Use https if dashboard container port is using https 

=======

2.0.70
++++++

**ACR**

* Fixed issue #9952 (a regression in the `acr pack build` command).
* Removed the default builder image name in `acr pack build`.

**Appservice**
* az webapp config ssl support to show a message if a resource is not found
* Fixed issue where `az functionapp create` does not accept Standard_RAGRS storage account type.
* Fixed an issue where az webapp up would fail if run using older versions of python

**Monitor**

* `metrics alert create`: Allow '/' and '.' characters in namespace name to support custom metrics.

**Network**

* network nic ip-config add: Fixes #9861 where --ids was inadvertently exposed but did not work.
* network application-gateway http-settings create/update: Fixes #9604. Add `--root-certs` to support user associate trusted root certificates with the HTTP settings.
* network dns record-set ns create: Fixes #9965. Support --subscription again by moving the supression into lower scope.
* network watcher test-ip-flow: Fixes #9845. Fixes #9844. Correct the error messages and help message for the `--vm` and `--nic` arguments. Only providing the name of the vm or nic without `--resource-group` will raise CLI usage error.

**RBAC**

* add "user update" command
* deprecate "--upn-or-object-id" from user related commands and introduce "--id"

**SQL**

* New Cmdlets for Management.Sql that supports Managed instance key and managed instance TDE protector management

**Storage**

* `storage remove`: add remove command for storage
* Fixed issue `storage blob update`.

**VM**

* list-skus: use newer api-version to output zone details
* vmss create: restore client end defaults to False for "--single-placement-group"
* snapshot/disk create: expose ZRS storage skus
* Add new command group `vm host` to support dedicated hosts. Expose `--host` and `--host-group` on `vm create`

2.0.69
++++++

**AKS**                                                                                                                                                                                                                                                                         * Fixed an issue where terminating the browse command always tried to call an endpoint that is only available within cloud shell, resulting in a connection failure in other environments

**Appservice**

* az webapp identity commands will return a proper error message if ResourceGroupName or App name are invalid.
* az webapp list fixed to return the correct value for numberOfSites if no ResourceGroup was provided.
* restore the idempotency of "appservice plan create" and "webapp create"

**Core**

* Fixed issue where `--subscription` would appear despite being not applicable.
* Added ossrdbmsResourceId to cloud.py.

**BATCH**

* Updated to Batch SDK and Batch Management Plane SDK to 7.0.0
* [Breaking] Replaced az batch pool node-agent-skus list with az batch pool supported-images list. The new command contains all of the same information originally available, but in a clearer format. New non-verified images are also now returned. Additional information about capabilities and batchSupportEndOfLife is accessible on the imageInformation object returned.
* When using --json-file option of az batch pool create network security rules blocking network access to a pool based on the source port of the traffic is now supported. This is done via the SourcePortRanges property on NetworkSecurityGroupRule.
* When using --json-file option of az batch task create and running a container, Batch now supports executing the task in the container working directory or in the Batch task working directory. This is controlled by the WorkingDirectory property on TaskContainerSettings.
* Fix error in --application-package-references option of `az batch pool create` where it would only work with defaults. Now it will properly accept specific versions as well.

**Eventhubs**

* Fix for issue #5824 - added validation for parameter --rights of authorizationrule commands

**RDBMS**

* Add optional parameter to specify replica SKU for create replica command.
* Fix the issue with CI test failure with creating MySQL replica.

**Relay**

* Fixed issue #8775 : Cannot create hybrid connection with disabled client authroization
* Added parameter "--requires-transport-security" to az relay wcfrelay create

**Servicebus**

* Fix for issue #5824 - added validation for parameter --rights of authorizationrule commands

**SQL**

* Improved error message when attempting to create a SQL resource which is not available in the specified region.

**Storage**

* Enable Files AADDS for storage account update.
* Fixed issue `storage blob service-properties update --set`.

2.0.68
++++++
**ACR**

* Support Timer Triggers for Task.

**Appservice**

* functionapp: `az functionapp create` enables application insights by default
* BREAKING CHANGE: (functionapp) removes deprecated `az functionapp devops-build` command. Please use the new command `az functionapp devops-pipeline` instead.
* functionapp: `az functionapp deployment config-zip` now works for Linux Consumption Function app plans

**Cosmos DB**

* Added support for disabling TTL

**DLS**

* Update ADLS version (0.0.45).

**Feedback**

* When reporting a failed extension command, `az feedback` now attempts to open the browser to the project/repo url of the
  extension from the index.

**HDInsight**

* BREAKING CHANGE: Changed "oms" command group name to "monitor"
* BREAKING CHANGE: Made "--http-password/-p" a required parameter
* Added completers for "--cluster-admin-account" and "cluster-users-group-dns" parameters completer
* "cluster-users-group-dns" parameter is now required when "—esp" is present
* Added a timeout for all existing argument auto-completers
* Added a timeout for transforming resource name to resource id
* Auto-completers can now select resources from any resource group. It can be a different resource group than the one specified with "-g"
* Added support for "--sub-domain-suffix" and "--disable_gateway_auth" parameters in the "az hdinsight application create" command

**Managed Services**

* Added support for API version 2019-06-01 (GA)

**NetAppFiles**

* Volume create/update: Added new argument --protocol-types
* Initial version relating to the R4 version of the RP.

**Profile**
* Suppress `--subscription` argument for logout command.

**IoT**

* Support for IoT Hub message enrichments

**RBAC**

* [BREAKING CHANGE] create-for-rbac: remove --password
* role assignment: expose --assignee-principal-type from create command to avoid intermittent
                   failures caused by AAD graph server replication latency
* ad signed-in-user: fix a crash on listing owned objects
* ad sp: use the right approach to find the application from a service principal

**RDBMS**

* Support storage auto-grow for MySQL, PostgreSQL and MariaDB

* Support replication for MariaDB.

**SQL**

* Document allowed values for sql db create --sample-name

**SQL VM**

* sql vm create/update: Added optional parameter `--sql-mgmt-type` to setup SQL management
* Minor fixes on SQL vm group that did not allow to update the key for storage accounts.

**VM**

* vmss create: Fix bug where command returns an error message when run with `--no-wait`. The command succesfully sends
  the request but returns failure status code and returns an error mesage.
* vm/vmss extension image list: Fix bug where command fails when used with --latest
* vmss create `--single-placement-group`: Removed client-side validation. Does not fail if `--single-placement-group` is
  set to true and`--instance-count` is greater than 100 or availability zones are specified, but leaves this validation
  to the compute service.
* vmss create `--platform-fault-domain-count`: Removed client-side validation. Allows platform fault domain count to be
  specified without specifying zone information, via `--zones`.

**Storage**

* storage blob generate-sas: User delegation SAS token support with --as-user
* storage container generate-sas: User delegation SAS token support with --as-user

2.0.67
++++++
* Introduced a new [Preview] status to tag to more clearly communicate to customers
  when a command group, command or argument is in preview status. This was previously
  called out in help text or communicated implicitly by the command module version number.
  The CLI will be removing version numbers for individual packages in the future, so this
  mechanism will be the sole way to communicate that a feature is in preview. Items which
  are not labeled as being in preview can be considered to be GA. Not that if a command is
  in preview, all of its arguments are as well, and, by extension, if a command group is
  labeled as being in preview, then all commands and arguments are considered to be in
  preview as well.

  As a result of this change, several command groups may seem to "suddenly" appear to be
  in a preview status with this release. What actually happened is that most packages were
  in a preview status, but are being deemed GA with this release.

2.0.66
++++++
* Minor fixes.

2.0.65
++++++
* Minor fixes.

2.0.64
++++++
* Minor fixes.

2.0.63
++++++
* Minor fixes.

2.0.62
++++++
* Minor fixes.

2.0.61
++++++
* Minor fixes.

2.0.60
++++++
* Minor fixes.

2.0.59
++++++
* Minor fixes.

2.0.58
++++++
* Pinning versions of command modules for pip install.

2.0.57
++++++
* Hot fix for issue 8399_.

.. _8399: https://github.com/Azure/azure-cli/issues/8399

2.0.56
++++++
* Minor fixes

2.0.55
++++++
* Minor fixes

2.0.54
++++++
* Minor fixes

2.0.53
++++++
* Minor fixes

2.0.52
++++++
* Minor fixes

2.0.51
++++++
* Minor fixes

2.0.50
++++++
* Minor fixes

2.0.49
++++++
* Minor fixes

2.0.48
++++++
* Fix Homebrew

2.0.47
++++++
* Minor fixes

2.0.46
++++++
* Minor fixes

2.0.45
++++++
* Minor fixes

2.0.44
++++++
* Minor fixes

2.0.43
++++++
* Minor fixes

2.0.42
++++++
* Minor fixes

2.0.41
++++++
* Minor fixes

2.0.40
++++++
* Minor fixes

2.0.39
++++++
* MSI packaging change

2.0.38
++++++
* Minor fixes

2.0.37
++++++
* Minor fixes

2.0.36
++++++
* Minor fixes

2.0.35
++++++
* Minor fixes

2.0.34
++++++
* Minor fixes

2.0.33
++++++
* Minor fixes

2.0.32
++++++
* Minor fixes

2.0.31
++++++
* Minor fixes

2.0.30
++++++
* Minor fixes

2.0.29
++++++
* Minor fixes

2.0.28
++++++
* Bug fix for 'ValueError: field 6 out of range (need a 48-bit value)' - https://github.com/Azure/azure-cli/issues/5184

2.0.27
++++++
* Minor fixes

2.0.26
++++++
* Minor fixes

2.0.25
++++++
* Minor fixes

2.0.24
++++++
* Minor fixes

2.0.23
++++++
* Minor fixes

2.0.22
++++++
* Remove `az component` commands. Use `az extension` instead. `az component` has been deprecated for several months now.

2.0.21
++++++
* Minor fixes

2.0.20
++++++

2.0.19 (2017-10-09)
+++++++++++++++++++
* no changes

2.0.18 (2017-09-22)
+++++++++++++++++++
* no changes

2.0.17 (2017-09-11)
+++++++++++++++++++
* no changes

2.0.16 (2017-08-31)
+++++++++++++++++++
* no changes

2.0.15 (2017-08-28)
+++++++++++++++++++
* no changes

2.0.14 (2017-08-15)
+++++++++++++++++++
* no changes

2.0.13 (2017-08-11)
+++++++++++++++++++
* no changes

2.0.12 (2017-07-28)
+++++++++++++++++++
* no changes

2.0.11 (2017-07-27)
+++++++++++++++++++
* Allow finer grained chunking for Data Lake Store transfer (#4014)

2.0.10 (2017-07-07)
+++++++++++++++++++
* no changes

2.0.9 (2017-06-21)
++++++++++++++++++
* no changes

2.0.8 (2017-06-13)
++++++++++++++++++
* no changes

2.0.7 (2017-05-30)
++++++++++++++++++

* Add billing modules to setup (#3465)

2.0.6 (2017-05-09)
++++++++++++++++++

* documentdb renamed to cosmosdb
* Add rdbms

2.0.5 (2017-05-05)
++++++++++++++++++

* Include Data Lake Analytics and Data Lake Store modules.
* Include Cognitive Services module.
* Include Service Fabric module.
* Include Interactive module.
* Remove Container module

2.0.4 (2017-04-28)
++++++++++++++++++

* Add 'az -v' as shortcut for 'az --version' (#2926)

2.0.3 (2017-04-17)
++++++++++++++++++

* Improve performance of package load and command execution (#2819)
* Alter JSON string parsing from shell (#2705)

2.0.2 (2017-04-03)
++++++++++++++++++

* Add acr, lab and monitor modules to default list.

2.0.1 (2017-03-13)
++++++++++++++++++

* Add 'az find' module

2.0.0 (2017-02-27)
++++++++++++++++++

* GA release.

0.1.2rc2 (2017-02-22)
+++++++++++++++++++++

* Fix format of package readme on PyPI.


0.1.2rc1 (2017-02-17)
+++++++++++++++++++++

* Handle cloud switching in more user friendly way + remove context
* Include the following command modules by default:

azure-cli-acs
azure-cli-appservice
azure-cli-batch
azure-cli-cloud
azure-cli-component
azure-cli-configure
azure-cli-container
azure-cli-documentdb
azure-cli-feedback
azure-cli-iot
azure-cli-keyvault
azure-cli-network
azure-cli-profile
azure-cli-redis
azure-cli-resource
azure-cli-role
azure-cli-sql
azure-cli-storage
azure-cli-vm


0.1.1b3 (2017-01-30)
++++++++++++++++++++

* Support Python 3.6.


0.1.1b2 (2017-01-19)
++++++++++++++++++++

* Modify telemetry code to be compatible with the change to azure-cli-core 0.1.1b2.


0.1.1b1 (2017-01-17)
++++++++++++++++++++

* [Tab completion] Enable zsh compatibility mode for zsh shell for 'pip' installed CLI.
* Modify telemetry code to be compatible with the change to azure-cli-core.

0.1.0b11 (2016-12-12)
+++++++++++++++++++++

* Preview release.
