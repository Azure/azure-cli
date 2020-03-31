.. :changelog:

Release History
===============

2.3.0
++++++

**ACR**

* 'az acr task update': null pointer exception
* `az acr import`: Modify help and error message to clarify the usage of --source and --registry
* Add a validator for argument 'registry_name'
* `az acr login`:Remove the preview flag on '--expose-token'
* [BREAKING CHANGE] 'az acr task create/update' Branch parameter is removed
* 'az acr task update' Customer now can update context, git-token, and or triggers individually
* 'az acr agentpool': new feature

**AKS**

* Fix apiServerAccessProfile when updating --api-server-authorized-ip-ranges
* aks update: Override outbound IPs with input values when update
* Do not create SPN for MSI clusters and support attach acr to MSI clusters

**AMS**

* Fix #12469: adding Fairplay content-key-policy fails due to problems with 'ask' parameter

**AppConfig**

* Add --skip-keyvault for kv export

**AppService**

* Fix #12509: Remove the tag to az webapp up by default
* az functionapp create: Updated --runtime-version help menu and added warning when user specifies --runtime-version for dotnet
* az functionapp create: Updated the way javaVersion was being set for Windows function apps

**ARM**

* az deployment create/validate: Use --handle-extended-json-format by default
* az lock create: Add examples of creating subresource in the help documentation
* az deployment {group/mg/sub/tenant} list: Support provisioningState filtering
* az deployment: Fix the parse bug for comment under the last argument

**Backup**

* Added multiple files restore capabilities
* Added support for Backing up OS Disks only
* Added restore-as-unmanaged-disk parameter to specify unmanaged restore

**Compute**

* az vm create: Add NONE option of --nsg-rule
* az vmss create/update: remove vmss automatic repairs preview tag
* az vm update: Support --workspace
* Fix a bug in VirtualMachineScaleSetExtension initialization code
* Upgrade VMAccessAgent version to 2.4
* az vmss set-orchestration-service-state: support vmss set orchestration service state
* Upgrade disk API version to 2019-11-01
* az disk create: add --disk-iops-read-only, --disk-mbps-read-only, --max-shares, --image-reference, --image-reference-lun, --gallery-image-reference, --gallery-image-reference-lun

**Cosmos DB**

* Fix missing --type option for deprecation redirections

**Docker**

* Update to Alpine 3.11 and Python 3.6.10

**Extension**

* Allow to load extensions in the system path via packages

**HDInsight**

* (az hdinsight create:) Support customers specify minimal supported tls version by using parameter `--minimal-tls-version`. The allowed value is 1.0,1.1,1.2

**IoT**

* Add codeowner
* az iot hub create : Change default sku to S1 from F1
* iot hub: Support IotHub in the profile of 2019-03-01-hybrid

**IoTCentral**

* Update error details, update default application template and prompt message

**KeyVault**

* Support certificate backup/restore
* keyvault create/update: Support --retention-days
* No longer display managed keys/secrets while listing
* az keyvault create: support `--network-acls`, `--network-acls-ips` and `--network-acls-vnets` for specifying network rules while creating vault

**Lock**

* az lock delete fix bug: az lock delete does not work on Microsoft.DocumentDB

**Monitor**

* az monitor clone: support clone metric rules from one resource to another
* Fix IcM179210086: unable to create custom metric alert for their Application Insights metric

**NetAppFiles**

* az volume create: Allow data protection volumes adding replication operations: approve, suspend, resume, status, remove

**Network**

* az network application-gateway waf-policy managed-rule rule-set add: support Microsoft_BotManagerRuleSet
* network watcher flow-log show: fix wrong deprecating info
* support host names in application gateway listener
* az network nat gateway: support create empty resource without public ip or public ip prefix
* Support vpn gateway generation
* Support `--if-none-match` in `az network dns record-set {} add-record`

**Packaging**

* Drop support for python 3.5

**Profile**

* az login: Show warning for MFA error

**RDBMS**

* Add server data encryption key management commands for PostgreSQL and MySQL
* Added support for minimal tls version and deny public access
* Bump the azure-mgmt-rdbms SDK version to 2.2.0
* Add --public-network-access to control whether a server supports public access or not

**Rest**

* az rest: Use configured ARM's resource ID

**REST**

* az rest: Dump request and response with `--verbose`

**Storage**

* az storage blob generate-sas: Fix #11643 to support encoding blob url
* az storage copy: Add parameter --content-type to fix#6466
* az storage account blob-service-properties update: Add --enable-versioning to support versioning for storage account * az storage account management-policy create: Add required flag for policy

2.2.0
++++++

**ACR**

* Fix: `az acr login` wrongly raise error
* Add new command `az acr helm install-cli`
* Add private link and CMK support
* add 'private-link-resource list' command

**AKS**

* fix the aks browse in cloud shell
* az aks: Fix monitoring addon and agentpool NoneType errors
* Add --nodepool-tags to node pool when creating azure kubernetes cluster
* Add --tags when adding or updating a nodepool to cluster
* aks create: add `--enable-private-cluster`
* add --nodepool-labels when creating azure kubernetes cluster
* add --labels when adding a new nodepool to azure kubernetes cluster
* add missing / in the dashboard url
* Support create aks clusters enabling managed identity
* az aks: Validate network plugin to be either "azure" or "kubenet"
* az aks: Add aad session key support
* [BREAKING CHANGE] az aks: support msi changes for GF and BF for omsagent (Container monitoring)(#1)
* az aks use-dev-spaces: Adding endpoint type option to the use-dev-spaces command to customize the endpoint created on an Azure Dev Spaces controller

**AppConfig**

* Unblock using "kv set" to add keyvault reference and feature …

**AppService**

* az webapp create : Fix issue when running the command with --runtime
* az functionapp deployment source config-zip: Add an error message if resource group or function name are invalid/don't exist
* functionapp create: Fix the warning message that appears with `functionapp create` today which cites a `--functions_version` flag but erroneously uses a `_` instead of a `-` in the flag name
* az functionapp create: Updated the way linuxFxVersion and container image name were being set for linux function apps
* az functionapp deployment source config-zip: Fix an issue caused by app settings change racing condition during zip deploy, giving 5xx errors during deployment
* Fix #5720946: az webapp backup fails to set name

**ARM**

* az resource: Improve the examples of the resource module
* az policy assignment list: Support listing policy assignments at Management Group scope
* Add `az deployment group` and `az deployment operation group` for template deployment at resource groups. This is a duplicate of `az group deployment` and `az group deployment operation`
* Add `az deployment sub` and `az deployment operation sub` for template deployment at subscription scope. This is a duplicate of `az deployment` and `az deployment operation`
* Add `az deployment mg` and `az deployment operation mg` for template deployment at management groups
* Add `az deployment tenant` and `az deployment operation tenant` for template deployment at tenant scope
* az policy assignment create: Add a description to the `--location` parameter
* az group deployment create: Add parameter `--aux-tenants` to support cross tenants

**CDN**

* Add CDN WAF commands

**Compute**

* az sig image-version: add --data-snapshot-luns
* az ppg show: add --colocation-status to enable fetching the colocation status of all the resources in the proximity placement group
* az vmss create/update: support automatic repairs
* [BREAKING CHANGE] az image template: rename template to builder
* az image builder create: add --image-template

**Cosmos DB**

* Add Sql stored procedure, udf and trigger cmdlets
* az cosmosdb create: add --key-uri to support adding key vault encryption information

**KeyVault**

* keyvault create: enable soft-delete by default

**Monitor**

* az monitor metrics alert create: support `~` in `--condition`

**Network**

* az network application-gateway rewrite-rule create: support url configuration
* az network dns zone import: --zone-name will be case insensitive in the future
* az network private-endpoint/private-link-service: remove preview label
* az network bastion: support bastion
* az network vnet list-available-ips: support list available ips in a vnet
* az network watcher flow-log create/list/delete/update: add new commands to manage watcher flow log and exposing --location to identify watcher explicitly
* az network watcher flow-log configure: deprecated
* az network watcher flow-log show: support --location and --name to get ARM-formatted result, deprecated old formatted output

**Policy**

* az policy assignment create: Fix the bug that automatically generated name of policy assignment exceeds the limit

**RBAC**

* az ad group show: fix --group value treated as regex problem

**RDBMS**

* Bump the azure-mgmt-rdbms SDK version to 2.0.0
* az postgres private-endpoint-connection: manage postgres private endpoint connections
* az postgres private-link-resource: manage postgres private link resources
* az mysql private-endpoint-connection: manage mysql private endpoint connections
* az mysql private-link-resource: manage mysql private link resources
* az mariadb private-endpoint-connection: manage mariadb private endpoint connections
* az mariadb private-link-resource: manage mariadb private link resources
* Updating RDBMS Private Endpoint Tests

**SQL**

* Sql midb Add: list-deleted, show-deleted, update-retention, show-retention
* (sql server create:) Add optional public-network-access 'Enable'/'Disable' flag to sql server create
* (sql server update:) make some customer-facing change
* Add minimal_tls_version property for MI and SQL DB

**Storage**

* az storage blob delete-batch: Misbehaving `--dryrun` flag
* az storage account network-rule add (bug fix): add operation should be idempotent
* az storage account create/update: Add Routing Preference support
* Upgrade azure-mgmt-storage version to 8.0.0
* az storage container immutability create: add --allow-protected-append-write parameter
* az storage account private-link-resource list: Add support to list private link resources for storage account
* az storage account private-endpoint-connection approve/reject/show/delete: Support to manage private endpoint connections
* az storage account blob-service-properties update: add --enable-restore-policy and --restore-days
* az storage blob restore: Add support to restore blob ranges

2.1.0
++++++

**ACR**

* Add a new argument `--expose-token` for `az acr login`
* Fix the incorrect output of `az acr task identity show -n Name -r Registry -o table`
* az acr login: Throw a CLIError if there are errors returned by docker command

**ACS**

* aks create/update: add `--vnet-subnet-id` validation

**Aladdin**

* Parse generated examples into commands' _help.py

**AMS**

* az ams is GA now

**AppConfig**

* Revise help message to exclude unsupported key/label filter
* Remove preview tag for most commands excluding managed identity and feature flags
* Add customer managed key when updating stores

**AppService**

* az webapp list-runtimes: Fix the bug for list-runtimes
* Add az webapp|functionapp config ssl create
* Add support for v3 function apps and node 12

**ARM**

* az policy assignment create: Fix the error message when the `--policy` parameter is invalid
* az group deployment create: Fix "stat: path too long for Windows" error when using large parameters.json file

**Backup**

* Fix for item level recovery flow in OLR
* Add restore as files support for SQL and SAP Databases

**Compute**

* vm/vmss/availability-set update: add --ppg to allowing updating ProximityPlacementGroup
* vmss create: add --data-disk-iops and --data-disk-mbps
* az vm host: remove preview tag for `vm host` and `vm host group`
* [BREAKING CHANGE] Fix #10728: `az vm create`: create subnet automatically if vnet is specified and subnet not exists
* Increase robustness of vm image list

**Eventhub**

* Azure Stack support for 2019-03-01-hybrid profile

**KeyVault**

* az keyvault key create: add a new value `import` for parameter `--ops`
* az keyvault key list-versions: support parameter `--id` for specifying keys
* Support private endpoint connections

**Network**

* Bump to azure-mgmt-network 9.0.0
* az network private-link-service update/create: support --enable-proxy-protocol
* Add connection Monitor V2 feature

**Packaging**

* [BREAKING CHANGE] Drop support for Python 2.7

**Profile**

* Preview: Add new attributes `homeTenantId` and `managedByTenants` to subscription accounts. Please re-run `az login` for the changes to take effect
* az login: Show a warning when a subscription is listed from more than one tenants and default to the first one. To select a specific tenant when accessing this subscription, please include `--tenant` in `az login`

**Role**

* az role assignment create: Fix the error that assigning a role to a service principal by display name yields a HTTP 400

**SQL**

* Update SQL Managed Instance cmdlet `az sql mi update` with two new parameters: tier and family

**Storage**

* [BREAKING CHANGE] `az storage account create`: Change default storage account kind to StorageV2

2.0.81
++++++

**ACS**

* Added support to set outbound allocated ports and idle timeouts on standard load balancer
* Update to API Version 2019-11-01

**ACR**

* [BREAKING CHANGE] `az acr delete` will prompt
* [BREAKING CHANGE] 'az acr task delete' will prompt
* Add a new command group 'az acr taskrun show/list/delete' for taskrun management

**AKS**

* Each cluster gets a separate service principal to improve isolation

**AppConfig**

* Support import/export of keyvault references from/to appservice
* Support import/export of all labels from appconfig to appconfig
* Validate key and feature names before setting and importing
* Expose sku modification for configuration store.
* Add command group for managed identity.

**AppService**

* Azure Stack: surface commands under the profile of 2019-03-01-hybrid
* functionapp: Add ability to create Java function apps in Linux
* functionapp: Added --functions-version property to 'az functionapp create'
* functionapp: Added support for node 12 for v3 function apps
* functionapp: Added support for python 3.8 for v3 function apps
* functionapp: Changed python default version to 3.7 for v2 and v3 function apps

**ARM**

* Fix issue #10246: `az resource tag` crashes when the parameter `--ids` passed in is resource group ID
* Fix issue #11658: `az group export` command does not support `--query` and `--output` parameters
* Fix issue #10279: The exit code of `az group deployment validate` is 0 when the verification fails
* Fix issue #9916: Improve the error message of the conflict between tag and other filter conditions for `az resource list` command
* Add new parameter `--managed-by` to support adding managedBy information for command `az group create`

**Azure Red Hat OpenShift**

* Add `monitor` subgroup to manage Log Analytics monitoring in Azure Red Hat OpensShift cluster

**CDN**

* Add support for rulesEngine feature
* Add new commands group 'cdn endpoint rule' to manage rules
* Update azure-mgmt-cdn version to 4.0.0 to use api version 2019-04-15

**Deployment Manager**

* Add list operation for all resources.
* Enhance step resource for new step type.
* Update azure-mgmt-deploymentmanager package to use version 0.2.0.

**BotService**

* Fix issue #11697: `az bot create` is not idempotent
* Change name-correcting tests to run in Live-mode only

**IoT**

* Deprecated 'IoT hub Job' commands.

**IoT Central**

* Update error details, update default application template and prompt message.
* Support app creation/update with the new sku name ST0, ST1, ST2.

**Key Vault**

* Add a new command `az keyvault key download` for downloading keys.

**Misc**

* Fix #6371: Support filename and environment variable completion in Bash

**NetAppFiles**

* Modified volume create to allow data protection volumes and added cmdlets for replication operations, approve, pause, resume and remove.

**Network**

* Fix #2092: az network dns record-set add/remove: add warning when record-set is not found. In the future, an extra argument will be supported to confirm this auto creation.

**Policy**

* Add new command `az policy metadata` to retrieve rich policy metadata resources
* `az policy remediation create`: Specify whether compliance should be re-evaluated prior to remediation with the `--resource-discovery-mode` parameter

**Profile**

* `az account get-access-token`: Add `--tenant` parameter to acquire token for the tenant directly, needless to specify a subscription

**RBAC**

* [BREAKING CHANGE] Fix #11883: `az role assignment create`: empty scope will prompt error

**Security**

* Added new commands `az atp show` and `az atp update` to view and manage advanced threat protection settings for storage accounts.

**SQL**

* `sql dw create`: deprecated `--zone-redundant` and `--read-replica-count` parameters. These parameters do not apply to DataWarehouse.
* [BREAKING CHANGE] `az sql db create`: Remove "WideWorldImportersStd" and "WideWorldImportersFull" as documented allowed values for "az sql db create --sample-name". These sample databases would always cause creation to fail.
* Add New commands `sql db classification show/list/update/delete` and `sql db classification recommendation list/enable/disable` to manage sensitivity classifications for SQL databases.
* `az sql db audit-policy`: Fix for empty audit actions and groups

**Storage**

* Add a new command group `az storage share-rm` to use the Microsoft.Storage resource provider for Azure file share management operations.
* Fix issue #11415: permission error for `az storage blob update`
* Integrate Azcopy 10.3.3 and support Win32.
* `az storage copy`: Add `--include-path`, `--include-pattern`, `--exclude-path` and`--exclude-pattern` parameters
* `az storage remove`: Change `--inlcude` and `--exclude` parameters to `--include-path`, `--include-pattern`, `--exclude-path` and`--exclude-pattern` parameters
* `az storage sync`: Add `--include-pattern`, `--exclude-path` and`--exclude-pattern` parameters

**ServiceFabric**

* Adding new commands to manage appliaction and services.
    - sf application-type
        - list
        - delete
        - show
        - create
    - sf application-type version
        - list
        - delete
        - show
        - create
    - sf application
        - list
        - delete
        - show
        - create
        - update
    - sf service
        - list
        - delete
        - show
        - create

2.0.80
++++++

**Compute**

* disk update: Add --disk-encryption-set and --encryption-type
* snapshot create/update: Add --disk-encryption-set and --encryption-type

**Storage**

* Upgrade azure-mgmt-storage version to 7.1.0
* `az storage account create`: Add `--encryption-key-type-for-table` and `--encryption-key-type-for-queue` to support Table and Queue Encryption Service

2.0.79
++++++

**ACR**

* [BREAKING CHANGE] Remove '--os' parameter for 'acr build', 'acr task create/update', 'acr run', and 'acr pack'. Use '--platform' instead.

**AppConfig**

* Add support for importing/exporting feature flags
* Add new command 'az appconfig kv set-keyvault' for creating keyvault reference
* Support various naming conventions when exporting feature flags to file

**AppService**

* Fix issue #7154: Updating documentation for command <> to use back ticks instead of single quotes
* Fix issue #11287: webapp up: By default make the app created using up 'should be 'SSL enabled'
* Fix issue #11592: Add az webapp up flag for html static sites

**ARM**

* Fix `az resource tag`: Recovery Services Vault tags cannot be updated

**Backup**

* Added new command 'backup protection undelete' to enable soft-delete feature for IaasVM workload
* Added new parameter '--soft-delete-feature-state' to set backup-properties command
* Added disk exclusion support for IaasVM workload

**Compute**

* Fix `vm create` failure in Azure Stack profile.
* vm monitor metrics tail/list-definitions: support query metric and list definitions for a vm.
* Add new reapply command action for az vm

**Misc.**

* Add preview command `az version show` to show the versions of Azure CLI modules and extensions in JSON format by default or format configured by --output

**Event Hubs**

* [BREAKING CHANGE] Remove 'ReceiveDisabled' status option from command 'az eventhubs eventhub update' and 'az eventhubs eventhub create'. This option is not valid for Event Hub entities.

**Service Bus**

* [BREAKING CHANGE] Remove 'ReceiveDisabled' status option from command 'az servicebus topic create', 'az servicebus topic update', 'az servicebus queue create', and 'az servicebus queue update'. This option is not valid for Service Bus topics and queues.

**RBAC**

* Fix #11712: `az ad app/sp show` does not return exit code 3 when the application or service principal does not exist

**Redis**

* Fixing `az redis update` operation to work for caches with RDB/AOF enabled

**Storage**

* `az storage account create`: Remove preview flag for --enable-hierarchical-namespace parameter
* Update azure-mgmt-storage version to 7.0.0 to use api version 2019-06-01
* Add new parameters `--enable-delete-retention` and `--delete-retention-days` to support managing delete retention policy for storage account blob-service-properties.

2.0.78
++++++

**ACR**

* Support Local context in acr task run

**ACS**

* [BREAKING CHANGE]az openshift create: rename `--workspace-resource-id` to `--workspace-id`.

**AMS**

* Update show commands to return 3 when resource not found

**AppConfig**

* Fix bug when appending api-version to request url. The existing solution doesn't work with pagination.
* Support showing languages besides English as our backend service support unicode for globalization.

**AppService**

* Fix issue #11217: webapp: az webapp config ssl upload should support slot parameter
* Fix issue #10965: Error: Name cannot be empty. Allow remove by ip_address and subnet
* Add support for importing certificates from Key Vault `az webapp config ssl import`

**ARM**

* Update azure-mgmt-resource package to use 6.0.0
* Cross Tenant Support for `az group deployment create` command by adding new parameter `--aux-subs`
* Add new parameter `--metadata` to support adding metadata information for policy set definitions.

**Backup**

* Added Backup support for SQL and SAP Hana workload.

**BotService**

* [BREAKING CHANGE] Remove '--version' flag from preview command 'az bot create'. Only v4 SDK bots are supported.
* Add name availability check for 'az bot create'.
* Add support for updating the icon URL for a bot via 'az bot update'.
* Add support for updating a Direct Line channel via 'az bot directline update'.
* Add '--enable-enhanced-auth' flag support to 'az bot directline create'.
* The following command groups are GA and not in preview: 'az bot authsetting'.
* The following commands in 'az bot' are GA and not in preview: 'create', 'prepare-deploy', 'show', 'delete', 'update'.
* Fix 'az bot prepare-deploy' changing '--proj-file-path' value to lower case (e.g. "Test.csproj" to "test.csproj").

**Compute**

* vmss create/update: Add --scale-in-policy, which decides which virtual machines are chosen for removal when a VMSS is scaled-in.
* vm/vmss update: Add --priority.
* vm/vmss update: Add --max-price.
* Add disk-encryption-set command group (create, show, update, delete, list).
* disk create: Add --encryption-type and --disk-encryption-set.
* vm/vmss create: Add --os-disk-encryption-set and --data-disk-encryption-sets.

**Core**

* Remove support for Python 3.4
* Plug in HaTS survey in multiple commands

**Cosmos DB**

* Update azure-mgmt-cosmosdb package to use 0.11.0
* az cosmosdb network-rule allows --vnet-name and --ignore-missing-endpoint as parameters

**DLS**

* Update ADLS sdk version (0.0.48).

**HDInsight**

* Support for creating a Kafka cluster with Kafka Rest Proxy
* Upgrade azure-mgmt-hdinsight to 1.3.0

**Install**

* Install script support python 3.8

**IOT**

* [BREAKING CHANGE] Removed --failover-region parameter from manual-failover. Now it will failover to assigned geo-paired secondary region.

**Key Vault**

* Fix #8095: `az keyvault storage remove`: improve the help message
* Fix #8921: `az keyvault key/secret/certificate list/list-deleted/list-versions`: fix the validation bug on parameter `--maxresults`
* Fix #10512: `az keyvault set-policy`: improve the error message when none of `--object-id`, `--spn` or `--upn` is specified
* Fix #10846: `az keyvault secret show-deleted`: when `--id` is specified, `--name/-n` is not required
* Fix #11084: `az keyvault secret download`: improve the help message of parameter `--encoding`

**Network**

* az network application-gateway probe: Support --port option to specify a port for probing backend servers when create and update
* az network application-gateway url-path-map create/update: bug fix for `--waf-policy`
* az network application-gateway: support `--rewrite-rule-set`
* az network list-service-aliases: Support list service aliases which can be used for Service Endpoint Policies
* az network dns zone import: Support .@ in record name

**Packaging**

* Add back edge builds for pip install
* Add Ubuntu eoan package

**Policy**

* Support for Policy API version 2019-09-01
* az policy set-definition: Support grouping within policy set definitions with `--definition-groups` parameter

**Redis**

* Add preview param `--replicas-per-master` to `az redis create` command
* Update azure-mgmt-redis from 6.0.0 to 7.0.0rc1

**ServiceFabric**

* Fixes in node-type add logic including #10963: Adding new node type with durability level Gold will always throw CLI error
* Update ServiceFabricNodeVmExt version to 1.1 in creation template

**SQL**

* Added "--read-scale" and "--read-replicas" parameters to sql db create and update commands, to support read scale management.

**SQL VM**

* New package upgrade 0.5.
* Add new --license-type supporting Disaster Recovery Benefit (DR).

**Storage**

* GA Release Large File Shares property for storage account create and update command
* GA Release User Delegation SAS token Support
* Add new commands `az storage account blob-service-properties show` and `az storage account blob-service-properties update --enable-change-feed` to manage blob service properties for storage account.
* [COMING BREAKING CHANGE] `az storage copy`: `*` character is no longer supported as a wildcard in URL, but new parameters --include-pattern and --exclude-pattern will be added with `*` wildcard support.
* Fix issue #11043: Support to remove whole container/share in `az storage remove` command

2.0.77
++++++

**ACR**

* Deprecated parameter `--branch` from acr task create/update

**Azure Red Hat OpenShift**

* Add `--workspace-resource-id` flag to allow creation of Azure Red Hat Openshift cluster with monitoring
* Add `monitor_profile` to create Azure Red Hat OpenShift cluster with monitoring

**AKS**

* Support cluster certificate rotation operation using "az aks rotate-certs".

**AppConfig**

* Add support for using ":" for `as az appconfig kv import` separator
* Fix issue for listing key values with multiple labels including null label.
* Update management plane sdk, azure-mgmt-appconfiguration, to version 0.3.0.

**AppService**

* Fix issue #11100: AttributeError for az webapp up when create service plan
* az webapp up: Forcing the creation or deployment to a site for supported languages, no defaults used.
* Add support for App Service Environment: az appservice ase show | list | list-addresses | list-plans | create | update | delete

**Backup**

* Fix issue in az backup policy list-associated-items. Added optional BackupManagementType parameter.

**Compute**

* Upgrade API version of compute, disks, snapshots to 2019-07-01
* vmss create: Improvement for --orchestration-mode
* sig image-definition create: Add --os-state to allow specifying whether the virtual machines created under this image are 'Generalized' or 'Specialized'
* sig image-definition create: Add --hyper-v-generation to allow specifying the hypervisor generation
* sig image-version create: Support --os-snapshot and --data-snapshots
* image create: Add --data-disk-caching to allow specifying caching setting of data disks
* Upgrade Python Compute SDK to 10.0.0
* vm/vmss create: Add 'Spot' to 'Priority' enum property
* [Breaking change] Rename '--max-billing' parameter to '--max-price', for both VM and VMSS, to be consistent with Swagger and Powershell cmdlets
* vm monitor log show: support query log over linked log analytics workspace.

**IOT**

* Fix #2531: Add convenience arguments for hub update.
* Fix #8323: Add missing parameters to create storage custom endpoint.
* Fix regression bug: Reverting the changes which overrides the default storage endpoint.

**Key Vault**

* Fix #11121: When using `az keyvault certificate list`, passing `--include-pending` now doesn't require a value of `true` or `false`

**NetAppFiles**

* Upgrade azure-mgmt-netapp to 0.7.0 which includes some additional volume properties associated with upcoming replication operations

**Network**

* application-gateway waf-config: deprecated
* application-gateway waf-policy: Add subgroup managed-rules to manage managed rule sets and exclusion rules
* application-gateway waf-policy: Add subgroup policy-setting to manage global configuration of a waf-policy
* [BREAKING CHANGE] application-gateway waf-policy: Rename subgroup rule to custom-rule
* application-gateway http-listener: Add --firewall-policy when create
* application-gateway url-path-map rule: Add --firewall-policy when create

**Packaging**

* Rewrite the az wrapper in Python
* Support Python 3.8
* Use Python 3 for RPM package

**Profile**

* Polish error when running `az login -u {} -p {}` with Microsoft account
* Polish `SSLError` when running `az login` behind a proxy with self-signed root certificate
* Fix #10578: `az login` hangs when more than one instances are launched at the same time on Windows or WSL
* Fix #11059: `az login --allow-no-subscriptions` fails if there are subscriptions in the tenant
* Fix #11238: After renaming a subscription, logging in with MSI will result in the same subscription appearing twice

**RBAC**

* Fix #10996: Polish error for `--force-change-password-next-login` in `az ad user update` when `--password` is not specified

**Redis**

* Fix #2902: Avoid setting memory configs while updating Basic SKU cache

**Reservations**

* Upgrading SDK Version to 0.6.0
* Add billingplan details info after calling Get-Gatalogs
* Add new command `az reservations reservation-order calculate` to calculate the price for a reservation
* Add new command `az reservations reservation-order purchase` to purchase a new reservation

**REST**

* `az rest` is now GA

**SQL**

* Update azure-mgmt-sql to version 0.15.0.

**Storage**

* storage account create: Add --enable-hierarchical-namespace to support filesystem semantics in blob service.
* Remove unrelated exception from error message
* Fix issues with incorrect error message "You do not have the required permissions needed to perform this operation." when blocked by network rules or AuthenticationFailed.

2.0.76
++++++

**ACR**

* Add a preview parameter `--pack-image-tag` to command `az acr pack build`.
* Support enabling auditing on creating a registry
* Support Repository-scoped RBAC

**AKS**

* Add `--enable-cluster-autoscaler`, `--min-count` and `--max-count` to the `az aks create` command, which enables cluster autoscaler for the node pool.
* Add the above flags as well as `--update-cluster-autoscaler` and `--disable-cluster-autoscaler` to the `az aks update` command, allowing updates to cluster autoscaler.

**AppConfig**

* Add appconfig feature command group to manage feature flags stored in an App Configuration.
* Minor bug fix for appconfig kv export to file command. Stop reading dest file contents during export.

**AppService**

* az appservice plan create: Adding support to set 'persitescaling' and app service environment on appservice plan create.
* Fixing an issue where webapp config ssl bind operation was removing existing tags from the resource
* Added "--build remote" flag for "az functionapp deployment source config-zip" to support remote build action during function app deployment.
* Change default node version on function apps to ~10 for Windows
* Add --runtime-version property to `az functionapp create`
* az appservice vnet-integration add: Fixed so that subnet delegation is case insensitive and delegating subnets does not overwrite previous data.


**ARM**

* deployment/group deployment validate: Add --handle-extended-json-format parameter to support multiline and comments in json template when deployment.
* bump azure-mgmt-resource to 2019-07-01

**Backup**

* Add AzureFiles backup support

**Compute**

* vm create: Add warning when specifying accelerated networking and an existing NIC together.
* vm create: Add --vmss to specify an existing virtual machine scale set that the virtual machine should be assigned to.
* vm/vmss create: Add a local copy of image alias file so that it can be accessed in a restricted network environment.
* vmss create: Add --orchestration-mode to specify how virtual machines are managed by the scale set.
* vm/vmss update: Add --ultra-ssd-enabled to allow updating ultra SSD setting.
* [BREAKING CHANGE] vm extension set: Fix bug where users could not set an extension on a VM with --ids.
* New commands `az vm image terms accept/cancel/show` to manage Azure Marketplace image terms.
* Update VMAccessForLinux to version 1.5

**CosmosDB**

* [BREAKING] sql container create: Change --partition-key-path to required parameter
* [BREAKING] gremlin graph create: Change --partition-key-path to required parameter
* sql container create: Add --unique-key-policy and --conflict-resolution-policy
* sql container create/update: Update the --idx default schema
* gremlin graph create: Add --conflict-resolution-policy
* gremlin graph create/update: Update the --idx default schema
* Fix typo in help message
* database: Add deprecation infomation
* collection: Add deprecation infomation

**IoT**

* Add new routing source type: DigitalTwinChangeEvents
* Fix #2826: Missing features in "az iot hub create"
* Bug Fixed: Return more descriptive message on raised exception.

**Key Vault**

* Fix #9352: Unexpected error when certificate file does not exist
* Fix #7048: `az keyvault recover/purge` not working

**Monitor**

* Updated azure-mgmt-monitor to 0.7.0
* az monitor action-group create/update: Added suport for following new receivers: Arm role, Azure app push, ITSM, automation runbook, voice, logic app and Azure function
* Included parameter usecommonalertschema for supported receivers
* Included parameter useaadwebhook for webhook receiver

**NetAppFiles**

* Upgrade azure-mgmt-netapp to 0.6.0 to use API version 2019-07-01. This new API version includes:

    - Volume creation --protocol-types accepts now "NFSv4.1" not "NFSv4"
    - Volume export policy property now named 'nfsv41' not 'nfsv4'
    - Volume creation-token renamed to file-path
    - Snapshot creation date now named just 'created'

**Network**

* az network private-dns link vnet create/update: Fixes #9851. Support cross-tenant virtual network linking.
* [BREAKING CHANGE] network vnet subnet list: Fix #10401. `--resource-group` and `--vnet-name` are required now.
* az network public-ip prefix create: Fix #10757. Support to specify IP address version (IPv4, IPv6) when creation
* Bump azure-mgmt-network to 7.0.0 and api-version to 2019-09-01
* az network vrouter: Support new service virtual router and virtual router peering
* az network express-route gateway connection: Support `--internet-security`

**Profile**

* Fix: `az account get-access-token --resource-type ms-graph` not working
* Remove warning from `az login`

**RBAC**

* Fix #10807: `az ad app update --id {} --display-name {}` doesn't work

**ServiceFabric**

* az sf cluster create: fix #10916 modify service fabric linux and windows template.json compute vmss from standard to managed disks

**SQL**

* Add "--compute-model", "--auto-pause-delay", and "--min-capacity" parameters to support CRUD operations for new SQL Database offering: Serverless compute model."

**Storage**

* storage account create/update: Add --enable-files-adds parameter and Azure Active Directory Properties Argument group to support Azure Files Active Directory Domain Service Authentication
* Expand `az storage account keys list/renew` to support listing or regenerating Kerberos keys of storage account.

2.0.75
++++++

**AKS**

* Set `--load-balancer-sku` default value to standard if supported by the kubernetes version
* Set `--vm-set-type` default value to virtualmachinescalesets if supported by the kubernetes version
* Add `az aks nodepool add`,`az aks nodepool show`, `az aks nodepool list`, `az aks nodepool scale`, `az aks nodepool upgrade`, `az aks nodepool update` and `az aks nodepool delete` commmands to support multiple nodepools in aks
* Add `--zones` to `az aks create` and `az aks nodepool add` commands to support availability zones for aks
* Enable GA support of apiserver authorized IP ranges via paramater `--api-server-authorized-ip-ranges` in `az aks create` and `az aks update`

**AMS**

* BREAKING CHANGE:
    content-key-policy create:
        - Changed parameter --ask from utf-8 string to 32 character hex string.
    job start:
        - Changed the command from `job start` to `job create`.

**AppConfig**

* Using & in authorization header
* Adding api-version to all requests
* Upgrading SDK Version to 1.0.0

**AppService**

* Added "webapp config access-restriction show | set | add | remove"
* az webapp up updated for better error-handling
* az appservice plan update support Isolated SKU

**ARM**

* az deployment create: Add --handle-extended-json-format parameter to support multiline and comments in json template.

**Backup**

* Enhanced error detail for vault delete in force mode.

**Compute**

* vm create: Add --enable-agent configuration.
* vm create: Use standard public IP SKU automatically when using zones.
* vm create: Compose a valid computer name from VM name if computer name is not provided.
* vm create: Add --workspace to enable log analytics workspace automatically.
* vmss create: Add --computer-name-prefix parameter to support custom computer name prefix of virtual machines in the VMSS.
* Update galleries API version to 2019-07-01.

**IoT**

* Fix #2116: Unexpected 'az iot hub show' error for resource not found.

**Monitor**

* az monitor log-analytics workspace: Support CRUD for Azure log analytics workspace.

**Network**

* az network private-dns link vnet create/update: Fixes #9851. Support cross-tenant virtual network linking.
* [BREAKING CHANGE] network vnet subnet list: Fix #10401. `--resource-group` and `--vnet-name` are required now.

**SQL**

* New Cmdlets for sql mi ad-admin that supports setting AAD administrator on Managed instance

**Storage**

* az storage copy: Add --preserve-s2s-access-tier parameter to preserve access tier during service to service copy.
* az storage account create/update: Add --enable-large-file-share parameter to support large file shares for storage account.

**RBAC**

* Fix #10493: az ad sp delete --id {} fails when application is not found. If not found, application deletion is skipped.

**Storage**

* Add support for WebAssembly (.wasm) mimetype detection

2.0.74
++++++

**ACR**

* Added a required `--type` parameter to command `az acr config retention update`
* Param `-n, --name` changed to `-r, --registry` for `az acr config` command group.

**AKS**

* Add `--load-balancer-sku`, `--load-balancer-managed-outbound-ip-count`, `--load-balancer-outbound-ips` and `--load-balancer-outbound-ip-prefixes` to `az aks create` command, which allows for creating AKS cluster with SLB.
* Add `--load-balancer-managed-outbound-ip-count`, `--load-balancer-outbound-ips` and `--load-balancer-outbound-ip-prefixes` to `az aks update` command, which allows for updating load balancer profile of an AKS cluster with SLB.
* Add `--vm-set-type` to `az aks create` command, which allows to specify vm types of an AKS Cluster (vmas or vmss).

**ARM**

* az group deployment create: Add --handle-extended-json-format to support multiline and comments in json template
* Update azure-mgmt-resource package to use 4.0.0

**Compute**

* vmss create: Add --terminate-notification-time parameters to support terminate scheduled event configurability.
* vmss update: Add --enable-terminate-notification and --terminate-notification-time parameters to support terminate scheduled event configurability.
* Update azure-mgmt-compute version to 8.0.0.
* vm/vmss create: Support --priority, --eviction-policy, --max-billing parameters.
* disk create: Allow specifying the exact size of the upload for customers who upload their disks directly.
* snapshot create: Support incremental snapshots for managed disks.

**Cosmos DB**

* Add `--type <key-type>` to `az cosmosdb keys list` command to show key, read only keys or connection strings
* Add `regenerate` to `az cosmosdb keys` group
* Deprecate `az cosmosdb list-connection-strings`, `az cosmosdb regenerate-key` and `az cosmosdb list-read-only-keys`

**EventGrid**

* Fix the endpoint help text to refer to the right parameter (namely, to point to parameter `--endpoint` rather than `--endpoint-type` in event subscription commands).

**Key Vault**

* Fix #8840: When using tenant domain name in `az login -t`, `keyvault create` fails. Tenant domain name is now resolved to GUID if it is not.

**Monitor**

* monitor metrics alert create: Fix #9901. Support special character `:` in `--condition` argument.

**Policy**

* Support for Policy new API version 2019-06-01.
* az policy assignment create: Add `--enforcement-mode` parameter for `az policy assignment create` command.

**Storage**

* Add --blob-type parameter for `az storage copy` command

2.0.73
++++++

**ACR**

* Added commands to configure retention policy (in preview): "az acr config retention"
* [BREAKING] Disable the pull request trigger by default for ACR Tasks
* az acr login --subscription: now supports cross tenant scenarios.

**AKS**

* Add support of ACR integration, which includes
* Add `--attach-acr <acr-name-or-resource-id>` to `az aks create` command, which allows for attach the ACR to AKS cluster.
* Add `--attach-acr <acr-name-or-resource-id>` and `--detach-acr <acr-name-or-resource-id>` to `az aks update` command, which allows to attach or detach the ACR from AKS cluster.

**Aladdin**

* Update Aladdin Service (az find) to v1.0 (GA)

**ARM**

* Update azure-mgmt-resource package to use 3.1.0, which utilizes API version 2019-05-10, allowing copy count to be zero.

**AppService**

* az webapp deployment source config-zip support for connection_verify
* Add support for ACR images with az webapp create

**Batch**

* Expanded `--json-file` capabilities of `az batch pool create` to allow for specifying MountConfigurations for file system mounts(see https://docs.microsoft.com/en-us/rest/api/batchservice/pool/add#request-body for structure)
* Expanded `--json-file` capabilities of `az batch pool create` with the optional property publicIPs on NetworkConfiguration. This allows specifying publicIPs to be used when deploying pools (see https://docs.microsoft.com/en-us/rest/api/batchservice/pool/add#request-body for structure)
* Expanded `--image` capabilities to support Shared Image Galleries images. Similar to the commands support for Managed Images, to use a Shared Image Gallery image simply use the ARM ID as the value to the argument.
* [BREAKING CHANGE] When not specified, the default value for `--start-task-wait-for-success` on `az batch pool create` is now true (was false).
* [BREAKING CHANGE] The default value for Scope on AutoUserSpecification is now always Pool (was Task on Windows nodes, Pool on Linux nodes). This argument is not exposed via the commandline, but can be set in the `--json-file` arguments.

**Cosmos DB**

* Update azure-mgmt-cosmosdb to latest python 0.8.0 library
* Populate DatabaseAccountCreateUpdateParameters with 2 new parameters to support Cassandra Connector Exchange(CCX) feature - enable_cassandra_connector, connector_offer

**HDInsight**

* `az hdinsight create`: Support customers specify minimal supported tls version by using parameter `--minimal-tls-version`. The allowed value is 1.0,1.1,1.2.
* `az hdinsight resize`: Make parameter `--workernode-count/-c` required
* GA release

**Key Vault**

* Fix #10286: Unable to delete subnet from network rules.
* Fix: Duplicated subnets and IP addresses can be added to network rules.

**Network**

* az network watcher flow-log: Fix #8132. Support `--interval` to set traffic analysis interval value.
* az network application-gateway identity: Fix #10073 and #8244 Add support for setting identity in application-gateway.
* az network application-gateway ssl-cert: Fix #8244. Add support for setting key vault id in application-gateway ssl-cert.
* az network express-route peering peer-connection: Fix #9404. Onboard `show` and `list` command for Azure express route peering peer connection resource.
* az network vnet-gateway create/update: Fix #9327. Support `--custom-routes` argument to set custom routes address space for VNet gateway and VPN client.
* az network express-route port identity: Fix #10747. Support to configure identity.
* az network express-route port link update: Fix #10747. Support to configure MACsec and enable/disable admin state.

**Policy**

* Support for Policy new API version 2019-01-01


**Storage**

* [BREAKING CHANGE] `az storage remove`: remove --auth-mode argument

2.0.72
++++++

**ACR**

* Move to 2019-05-01 api-version, which follows replace semantics for ACR resource creation.
* Breaking change: Classic SKU no longer supported.

**API Management**

* Introduced initial impementation of API Management preview commands (az apim)

**AppConfig**

* Added "appconfig kv restore" command.

**AppService**

* Fixed az webapp webjob continuous start command when specifying a slot.
* az webapp up detects env folder and removes it from compressed file used for deployment

**Backup**

* Added Support for managed disk restore, InstantRP

**keyvault**

* Fix the bug in secret set command that ignores the expires argument

**Network**

* az network lb create/frontend-ip create: Fixes #10018. Support `--private-ip-address-version` argument to create IPv6 based private-ip-address
* az network private-endpoint create/update/list-types: Fixes #9474. Support create/update/list-types commands for private endpoint.
* az network private-link-service: Fixes #9475. Onboard commands for private link service.
* az network vnet subnet update: Support `--private-endpoint-network-policies` and `--private-link-service-network-policies` arguments for update command.

**RBAC**

* Fix #10151 - `az ad app update --homepage` not updating homepage.
* Derive service principal's display name from name in the create-for-rbac command

**ServiceFabric**

* Fix for issues #7145,  #7880 and #7889 - fix for key vault and cert issues when creating a cluster.
* Fix for issue #7130 - fix add cert command. Using the cluster resource group when the key vault resource group is not specified.
* Fix for issue #9711 - fix command 'cluster setting set' command. Using named parameters for SettingsSectionDescription constructor.

**SignalR**

* signalr cors: New command to manage SignalR CORS
* az signalr create: --service-mode: new service mode argument
* signalr restart: new command to restart the service
* signalr update: new command to update the service

**Storage**

* Add `revoke-delegation-keys` command for storage account

2.0.71
++++++

**AppService**

* az webapp webjob continuous group commands were failing for slots
* fixes an issue where `az webapp deployment container config` displayed the wrong Docker CI/CD webhook URL for some apps

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
