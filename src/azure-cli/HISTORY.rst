.. :changelog:

Release History
===============

2.37.0
++++++

**ACR**

* Fix some `az acr manifest` commands do not correctly handle `-u/-p` credentials resulting in auth failure when not logged in to `az cli` (#22497)
* Fix some `az acr` commands do not handle certain next-link tokens correctly resulting in exceptions when paging (#22497)
* Fix some `az acr manifest` commands do not correctly parse some FQDNs resulting in exceptions (#22497)

**AKS**

* [BREAKING CHANGE] `az openshift`: Remove the deprecated command group (#22286)
* `az aks create`: Add new option `--node-resource-group` to specify the name of the resource group where user resources are stored (#22357)
* `az aks get-credentials`: Raise exception when existing config file is invalid (#22359)
* `az aks check-acr`: Add new option `--node-name` to specify the name of a specific node to perform acr pull test checks (#22358)
* Fix #22032: `az aks nodepool add/update`: Fix autoscaler parameters for user node pools (#22442)
* `az aks create/update`: Add Microsoft Defender security profile support (#22217)
* GA Kubernetes version alias (#22456)
* `az aks update`: Add support for updating kubelet identity with `--assign-kubelet-identity` (#22493)

**API Management**

* Fix apim's `apply-network-updates` command (#22180)

**App Service**

* Fix #18151: `az webapp config backup restore`: Fix the bug that 'WebAppsOperations' object has no attribute 'restore_slot' (#22365)

**ARM**

* `az resourcemanagement private-link create`: Create Resource management private link (#22064)
* `az resourcemanagement private-link delete`: Delete Resource management private link (#22064)
* `az resourcemanagement private-link show`: Get Resource management private link (#22064)
* `az resourcemanagement private-link list`: List Resource management private link (#22064)
* `az private-link association create`: Create private link association (#22064)
* `az private-link association delete`: Delete private link association (#22064)
* `az private-link association show`: Get private link association (#22064)
* `az private-link association list`: List private link association (#22064)
* `az group delete`: Add new parameter `--force-deletion-types` to support force deletion (#22184)
* `az bicep restore`: Add new command to restore external modules (#22423)
* `az bicep build`: Add new parameter `--no-restore` to allow compilation without restoring external modules (#22423)
* `az bicep decompile`: Add new parameter `--force` to allow overwriting existing Bicep files (#22423)
* `az resource wait`: Fix `--created` keeps waiting even when `az resource show` returns "provisioningState": "Succeeded" (#22254)

**ARO**

* `az aro create`: Add support for FIPS modules, host encryption, and disk encryption for master and worker nodes (#22320)

**Backup**

* `az backup vault resource-guard-mapping`: Add support for updating, showing, and deleting ResourceGuardProxy (#22472)
* Add multiple user authentication (MUA) support for critical operations: `az backup vault backup-properties set`/`az backup item set-policy`/`az backup policy set`/`az backup protection disable` (#22472)
* Add `--tenant-id` parameter in critical commands: `az backup vault backup-properties set`/`az backup item set-policy`/`az backup policy set`/`az backup protection disable`/`az backup vault resource-guard-mapping` for cross-tenant scenario (#22472)

**Compute**

* `az vm image list`: Add new server version aliases `Win2022AzureEditionCore` for offline list (#22193)
* `az vm update`: Add additional license type SLES for `--license-type` (#22336)
* `az vmss create`: Support enabling single placement group for Flexible VMSS (#22291)
* `az disk create/update`: Add new parameter `--data-access-auth-mode` to support data access authentication mode (#22175)
* `az sig show`: Add new parameter `--sharing-groups` to support query shared gallery group (#22371)
* `az vm host group create`: Add new parameter `--ultra-ssd-enabled` to support Ultra SSD (#22176)

**Cosmos DB**

* `az cosmosdb sql container update`: Fix bug to accept analyticalStorageTTL arg (#22132)

**Event Hubs**

* `az eventhubs namespace schema-registry`: Add cmdlets for schema registry (#22100)

**Identity**

* `az identity list-resources`: Add new command to support list the associated resources for identity (#22519)

**IoT**

* `az iot dps policy` and `az iot dps linked-hub`: Fix DPS state updating (#22259)
* `az iot central app private-link-resource list`: Add a new command to support listing private link resources (#22273)
* `az iot central app private-endpoint-connection show`: Add a new command to support showing details of a private endpoint connection of the IoT Central app (#22273)
* `az iot central app private-endpoint-connection approve`: Add a new command to support approving a private endpoint connection for the IoT Central app (#22273)
* `az iot central app private-endpoint-connection reject`: Add a new command to support rejecting a private endpoint connection for the IoT Central app (#22273)
* `az iot central app private-endpoint-connection delete`: Add a new command to support deleting a private endpoint connection for the IoT Central app (#22273)

**Key Vault**

* Fix#22457: `az keyvault key decrypt/encrypt`: Fix returning bytes for `--output tsv` (#22464)

**Monitor**

* [BREAKING CHANGE] `az monitor alert`: Deprecate whole command group, please use `monitor metrics alert` (#22507)
* [BREAKING CHANGE] `az monitor autoscale-settings`: Deprecate whole command group, please use `az monitor autoscale` (#22507)
* [BREAKING CHANGE] `az monitor activity-log list`: Deprecate parameter `--filters`. (#22507)
* [BREAKING CHANGE] `az monitor activity-log list`: Deprecate parameter flag `--resource-provider`, please use `--namespace` (#22507)

**NetAppFiles**

* `az netappfiles volumes export-policy add`: Fix `rule-index` validation and parameter made non required (#22255)
* `az netappfiles ad add`: Add new optional parameter `site` (#22155)
* `az netappfiles ad update`: Add new optional parameter `site` (#22155)

**Network**

* `az network watcher connection monitor create`: Change for using user-provided workspace-ids even if output-type is missing (#22156)
* `az network dns zone export`: Support traffic manager resources (#22205)
* Private link add `Microsoft.Kusto/clusters` provider (#22178)
* `az network lb create`: Add warnings for default SKU (#22339)
* `az network lb address-pool`: Support connection draining on load balancer (#22508)
* `az network application-gateway`: Add `settings`, `listener` and `routing-rule` command groups (#22489)
* `az network application-gateway create`: Add parameter `--priority` (#22489)
* `az network application-gateway probe`: Add parameter `--host-name-from-settings` (#22489)

**Packaging**

* Bump embedded Python to 3.10 for deb packages (#22170)
* Use Mariner 2.0 GA image to build RPM (#22427)

**RDBMS**

* `az mariadb server create/update`: Support `--minimal-tls-version` (#22258)
* Change MySQL MemoryOptimized tier name to BusinessCritical (#22241)

**Reservations**

* Update Reservation command with latest SDK (#22197)

**Role**

* [BREAKING CHANGE] `az az/role`: Migrate the underlying API of `az ad` and `az role` from AD Graph API to Microsoft Graph API. For more details, see [Microsoft Graph migration](https://docs.microsoft.com/en-us/cli/azure/microsoft-graph-migration) (#22432)

**Security**

* `az security alerts-suppression-rule`: Add alerts suppression rules to security module (#22014)

**Service Bus**

* `az servicebus queue update`: Fix message time to live (#22218)
* `az servicebus queue`: Adding ReceiveDisabled to --status (#22460)
* `az servicebus namespace create/update`: Add `--disable-local-auth` to enable or disable SAS authentication (#19741)
* `az servicebus namespace private-endpoint-connection/private-link-resource`: New command groups (#19741)

**Service Connector**

* [BREAKING CHANGE] `az containerapp connection create`: Default client_type changed to `none` (#22311)
* `az containerapp connection`: Add new command group to support container app connection (#22290)
* `az containerapp connection create`: Add `--container` parameter in interactive mode (#22311)
* `az spring connection`: Add support for `az sping-cloud` renaming (#22356)
Add new parameter key value pair to support password from KeyVault (#22319)

**Service Fabric**

* `az sf cluster node-type add`: Fix the unexpected error that 'StorageAccountsOperations' object has no attribute 'create' (#22283)

**SQL**

* Fix #22316: `az sql server ad-admin create`: Fix Display Name and Object ID to be required (#22343)

**SQL VM**

* `az sql vm update`: Add configuration options for SQL Best Practices Assessment (#21281)

**Storage**

* [BREAKING CHANGE] `az storage share show`: Remove contentLength, hasImmutabilityPolicy and hasLegalHold from the output result (#22215)
* [BREAKING CHANGE] `az storage blob snapshot`: Now only returns version info instead of all blob properties (#22309)
* Fix #21819: `az storage fs directory`: Add new command `generate-sas` (#22152)
* `az storage account show-connection-string`: Append endpoints by default (#22280)
* Fix #22236: `az storage entity insert`: Fix `--if-exists fail` not working (#22334)
* `az storage copy`: Fix `--exclude-path` TypeError (#22367)
* `az storage blob download`: Allow downloading to stdout for pipe support (#22317)
* Fix #22209: `az storage entity insert`: Fix `Edm.Boolean` not working (#22483)
* `az storage directory/file list`: Add `--exclude-extended-info` to exclude some properties info from response, default to `False` (#22490)
* Fix #21781 `az storage blob upload/download`: Progress fix (#22504)
* `az stroage entity query`: Fix UUID type is not JSON serializable (#22492)
* `az storage blob delete-batch`: No longer exits after individual delete failure (#22309)

2.36.0
++++++

**ACR**

* `acr task run`: Add `--no-format` option (#21983)
* `acr task logs`: Add `--no-format` option (#21983)
* `acr taskrun logs`: Add `--no-format` option (#21983)

**AKS**

* `az aks create`: Add `--nat-gateway-managed-outbound-ip-count` and `--nat-gateway-idle-timeout` to support nat gateway integration (#21623)
* `az aks create`: Add `managedNATGateway` and `userAssignedNATGateway` to supported outbound type (#21623)
* `az aks check-acr`: Bump canipull to 0.0.4-alpha to skip location check if cname returns only privatelink (#22092)

**AMS**

* `az ams asset-track create`: Add command to create an asset track (#22056)
* `az ams asset-track show`: Add command to show an asset track (#22056)
* `az ams asset-track list`: Add command to list all tracks under an asset (#22056)
* `az ams asset-track update`: Add command to update the parameters of a track (#22056)
* `az ams asset-track update-data`: Add update-data command to refresh the server in case track file was updated (#22056)
* `az ams asset-track delete`: Add command to delete track (#22056)
* `az ams streaming-endpoint get-skus`: Add command to get skus under a streaming endpoint (#22056)

**App Config**

* Fix feature flag import for missing description when using 'appconfig/kvset' profile (#21941)

**App Service**

* `az staticwebapp create`: Allow creating Static Web Apps not connected to a github repo (#22042)
* Fix #21943: `az webapp config backup create`: Fix AttributeError 'str' object has no attribute 'get' (#22024)

**Backup**

* `az backup policy create/set`: Add support for creating/updating IaaSVM MBPD policy (#22105)

**Bot Service**

* `az bot directline/email/facebook/kik/msteams/skype/slack/sms/telegram create`: Add `--location` argument as specified by user to channel creation for regionality/EUDB (#21908)

**CDN**

* `az afd rule create`: Fix rule creation failure with action type RouteConfigurationOverride (#21975)
* `az afd route create`: Fix route creation issue with disabled `--link-to-default-domain option` (#21975)
* Fix #22066: `az cdn name-exists` missing type argument (#22139)

**Compute**

* `az vm create`: Fix the bug of "NoneType object has no attribute lower" when creating Flex VMSS without `--vm-sku` parameter (#22016)
* `az restore-point create`: Add a new parameter `--source-restore-point` to support cross region copy (#21841)
* `az restore-point show`: Add a new parameter `--instance-view` to show the instance view of a restore point and replace the deprecated `--expand` (#21841)
* `az restore-point collection show`: Add a new parameter `--restore-points` to show all contained restore points in the restore point collection and replace the deprecated `--expand` (#21841)
* `az sig image-version create`: Add new parameter `--target-region-cvm-encryption` to support Confidential VM encrypting the OS disk (#22091)
* `az vm/vmss create`: Install guest attestation extension and enable system managed identity by default when Trusted Launch configuration is met (#22048)
* `az vm/vmss create`: Add new parameter `--disable-integrity-monitoring` to disable the default behavior (installing guest attestation extension and turning on MSI) when creating VM/VMSS compliant with Trusted Launch (#22048)

**IoT**

* [BREAKING CHANGE] `iot dps access-policy`: Deprecate access-policy in favor of policy (#21928)

**Key Vault**

* `az keyvault key`: GA SKR and keyvault key rotation (#21989)
* Fix #20520: `az keyvault network-rule`: Support removing multiple IP (#22025)

**NetAppFiles**

* `az netappfiles volume-group`: Add command group to manage volume group resources (#21897)

**Network**

* Fix #21845: `az network routeserver create` required `--public-ip-address` argument (#21864)
* Fix #21829: `az network traffic-manager endpoint update` required `--type` argument (#21895)
* Private link add `Microsoft.Network/privateLinkServices` provider (#21986)
* Fix #22085: `az network nsg rule create` has no attribute "is_default" (#22109)

**Packaging**

* Release DEB package for Ubuntu 22.04 Jammy Jellyfish (#21948)
* Release RPM package for RHEL 8, CentOS Stream 8 (#21655)
* Release RPM package for Mariner 1.0, 2.0 preview (#22034)

**RDBMS**

* `az postgres server create`: Fix error message for invalid server names (#22019)

**Security**

* Add `az security automation` CLI commands (#21942)

**Service Bus**

* `az servicebus namespace create`: Add zone redundant parameter (#22099)
* `az servicebus namespace authorization-rule keys renew`: Add `--key-value` parameter (#22115)

**Service Connector**

* `az webapp connection`: Add command `create sql/webpubsub` to support more target resources (#21894)

**SQL**

* `az sql mi create`, `az sql mi update`: Add `--service-principal-type` parameter to support Win Auth (Kerberos) (#21872)

**Storage**

* Fix #21914: `az storage blob upload`: Make block size larger (100MB) for large files (>200GB) (#21971)
* `az storage account/container/blob generate-sas`: Add `--encryption-scope` (#21990)
* Fix #21920: `az storage copy`&`az storage remove`: Hide credentials in warning message (#21980)
* Add `--blob-endpoint/--file-endpoint/--table-endpoint/--queue-endpoint` for data service commands to support customized service endpoint (#21782)
* GA storage file datalake soft delete (#22037)
* `az storage cors add`: Allow `PATCH` for `--methods` (#22045)
* `az storage entity`: Support specifying `EdmType` for `--entity` (#22060)
* Fix #21966: `az storage blob download-batch`: Fix failure when `--pattern` is blob name (#22072)
* Fix #21414: `az storage blob sync`: Fix the flag `--delete-destination` default to false (#21662)
* `az storage account blob-inventory-policy create`: Add missing fields, add excludePrefix in filter (#22088)

2.35.0
++++++

**ACR**

* [BREAKING CHANGE] `az acr create`: Reject request with a name using uppercase letters (#21162)
* [BREAKING CHANGE] `az acr connected-registry create`: Reject request with a name using uppercase letters (#21162)
* `az acr update`: Disable public network now displays a warning message (#21162)
* Deprecate `az acr manifest metadata` command group (#21639)
* `az acr manifest`: Add `show-metadata`, `list-metadata` and `update-metadata` commands (#21639)

**AKS**

* `az aks create/update`: Add new parameters `--enable-gmsa`, `--gmsa-dns-server`, `--gmsa-root-domain-name` to support Windows gMSA v2 (#21472)
* `aks enable-addons`: Add new parameter `--enable-msi-auth-for-monitoring` to support enabling managed identity auth (#21661)
* `az aks snapshot create`: Move to `az aks nodepool snapshot create` (#21836)
* `az aks snapshot delete`: Move to `az aks nodepool snapshot delete` (#21836)
* `az aks snapshot list`: Move to `az aks nodepool snapshot list` (#21836)
* `az aks snapshot show`: Move to `az aks nodepool snapshot show` (#21836)
* `az aks create`: Add `--pod-subnet-id` to support dynamically assigne pod ip (#21651)
* `az aks nodepool add`: Add `--pod-subnet-id` to support dynamically assigne pod ip (#21651)
* `az aks create`: Add `--kubelet-config` and `--linux-os-config` to support custom node configuration (#21722)
* `az aks nodepool add`: Add `--kubelet-config` and `--linux-os-config` to support custom node configuration (#21722)

**AMS**

* `az ams account identity assign`: Add ability to assign managed identity to media services account (#21795)
* `az ams account identity remove`: Add ability to assign managed identity to media services account (#21795)
* `az ams transform create`: Add new parameter `blur-type` for FaceDetector presets (#21795)
* `az ams account encryption set`: Add new parameters `system-assigned` and `user-assigned` to allow users to set managed identities to their account encryption (#21795)
* `az ams account storage set-authentication`: Add new parameters `system-assigned` and `user-assigned` to allow users to set managed identities for their storage account attached to Media Services (#21795)

**APIM**

* `apim api schema create`: Add new command to support creating a schema for graphql API (#21585)
* `apim api schema delete`: Add new command to support deleting the schema of an API (#21585)
* `apim api schema list`: Add new command to support showing the list of schema's of an API (#21585)
* `apim api schema show`: Add new command to support getting the schema of an API (#21585)
* `apim api schema entity`: Add new command to support getting the schema entity tag (#21585)
* Onboard to private endpoint for API Management (#21776)

**App Config**

* `az appconfig kv export`: Stop throwing error if no key-values are exported to App Service (#21518)
* `az appconfig create`: Add new options `retention-days` and `enable-purge-protection` (#21362)
* `az appconfig list-deleted`: Add new command to list all deleted but not yet purged App Configurations (#21362)
* `az appconfig show-deleted`: Add new command to show properties of a deleted but not yet purged App Configuration (#21362)
* `az appconfig recover`: Add new command to recover a deleted but not yet purged App Configuration (#21362)
* `az appconfig purge`: Add new command to purge a deleted store (#21362)

**App Service**

* Fix #21439: `az webapp deploy`: Fix `--async` argument value in help message (#21442)
* Fix #21574: `az webapp vnet-integration add`: Fix the AttributeError that 'NoneType' object has no attribute 'server_farm_id' (#21636)
* `az staticwebapp create` : Change default output location and API location to `None`. Change default app location to "/". Remove unnecessary properties from output (#20955)
* `az staticwebapp show` : Remove unnecessary properties from output (#20955)
* `az staticwebapp list` : Remove unnecessary properties from output (#20955)
* `az staticwebapp update` : Remove unnecessary properties from output (#20955)
* `az webapp deployment slot create`: Allow overriding container settings (#21309)
* Fix #21080: `az webapp up`: Fix object has no attribute 'response' (#21556)
* Fix #19747: `az webapp up`: Fix TypeError: 'NoneType' object is not iterable (#21556)
* `az webapp up`: Validate that ASE exists, is an ASE v3, and not an ILB ASE; Validate that preexisting plan is on the ASE; Default to I1V2 SKU if using an ASE (#21556)
* Fix #20240: `az functionapp deployment source config-zip`: Fix the bug that the parameter `--slot` doesn't work (#21698)
* Fix #12090: `az webapp create`: Allow plan in different resource group from web app (#21469)
* `az staticwebapp identity assign`, `az staticwebapp hostname set`, `az staticwebapp create`: Fix #21186: Show detailed error message instead of "bad request" (#21812)
* `az staticwebapp update`: Fix #21465: Allow specifying static web app resource group (#21812)
* Fix #21728: `az webapp deployment github-actions add`: Allow passing in runtime with colon delimiter (#21771)
* `az webapp config`: Fix for Web App Persistent Storage gets disabled after each deployment (#21385)
* `az appservice ase create-inbound-services`: Add support for Azure private DNS zone creation in ASEv3 (#21528)

**ARM**

* Fix #20842: `az bicep`: Fix to use requests environment variables for CA bundle (#21807)
* `az policy assignment create`: Support `--subscription` parameter (#21839)

**Backup**

* List commands multi-page response bug fix (#21643)
* `az backup restore restore-disks`: Add support for Original Location Restore and Alternate Location Restore (#21643)
* `az backup policy create/set/list`: Add support for creating and selectively listing Enhanced policies (#21643)
* `az backup protection enable-for-vm`: Add support for Trusted VM configure protection with Enhanced policies (#21643)
* `az backup vault backup-properties`: Add new parameter `--hybrid-backup-security-features` to support setting the security features for hybrid backups (#21736)

**CDN**

* Upgrade azure-mgmt-cdn to 12.0.0 for Azure Front Door Standard/Premium GA (#21786)

**Cognitive Services**

* Upgrade to use API 2022-03-01 (#21850)
* Add new command `az cognitiveservices account list-models` (#21850)

**Compute**

* [BREAKING CHANGE] `az vm/vmss create`: Remove the default value `Contributor` of parameter `--role` (#21474)
* `az vm host`: Add new command `restart` to support dedicated host reboot (#20923)
* `az vm extension show`: Add new parameters `--instance-view` to support track the vm extension progress (#21547)
* Change help info of `--enable-bursting` to flag it is for on-demand only (#21653)
* Fix #20174: `az vm create`: Determine plan information when using image alias (#21666)
* `az disk/snapshot/sig definitiion create/update`: Add new parameters `--architecture` to support ARM64 (#21641)
* `az vm disk attach`: Add new parameter `--disks` to support attaching multiple disks in one API call (#21545)
* `az vm/vmss create`: Support creating VM/VMSS from community gallery image (#21843)
* `az vm/vmss create`: Add community gallery legal agreement acceptance (#21843)
* `az vm/vmss create`: Add the verification of whether `--os-type` is correct when creating VM from community gallery image or shared gallery image (#21843)

**Cosmos DB**

* `az cosmosdb update`: Support updating key vault key uri (#21410)
* `az managed-cassandra cluster update`: Allow `--external-seed-nodes`, `--external-gossip-certificate` and `--client-certificate` to take empty list (#21837)
* `az managed-cassandra cluster`: Fix `--repair-enabled` as of type three_state_flag (#21595)

**Event Grid**

* Fix #21521: System topic subscription update attribute error (#21615)
* Support user identity and mixed mode (#21648)

**Event Hubs**

* `az eventhub namespace update`: Fix disable eventhub capture and autoinflate (#21816)

**Key Vault**

* Fix #18319 & #21555: `az keyvault list-deleted`: List all deleted resources if no specified resource type (#18411)
* `az keyvault key create`: Support `--default-cvm-policy` (#21527)
* Fix #21330: `az keyvault network-rule remove`: Fix ip address remove issue (#21630)

**NetAppFiles**

* `az netappfiles snapshot restore-files`: New command to restore specified files from the specified snapshot to the active filesystem (#21712)
* `az netappfiles volume create`: Add optional parameters `--enable-subvolumes` (#21712)
* `az netappfiles volume delete`: Add optional parameter `--force-delete` or `--force` (#21712)
* `az netappfiles volume update`: Add optional parameter `--unix-permissions` (#21712)
* `az netappfiles subvolume`: New command group to manage subvolume resources (#21712)
* `az netappfiles subvolume create`: New command to create subvolume (#21712)
* `az netappfiles subvolume show`: New command to get specified subvolume (#21712)
* `az netappfiles subvolume update`: New command to update specified subvolume (#21712)
* `az netappfiles subvolume list`: New command to get all subvolume in a specified volume (#21712)
* `az netappfiles subvolume delete`: New command to delete specified subvolume (#21712)
* `az netappfiles subvolume metadata`: New command group to manage subvolume metadata resources (#21712)
* `az netappfiles subvolume metadata show`: New command to get details about a specified subvolume (#21712)
* `az netappfiles account ad add`: New optional parameters to support ldap search scope `--user-dn`, `--group-dn` and `--group-filter` (#21712)
* `az netappfiles account ad update`: New optional parameters to support ldap search scope `--user-dn`, `--group-dn` and `--group-filter` (#21712)

**Network**

* `az network nat gateway`: Validate attaching public IPs (#21483)
* `az network lb`: Support inbound NAT rule port mapping query (#21482)
* Fix #21716: `az network private-dns zone import`: Allow hyphenated SRV records (#21717)
* `az network application-gateway waf-policy managed-rule exclusion rule-set`: Support pre-rule exclusion creation without exclusion (#21879)

**Packaging**

* Use Red Hat Universal Base Image 8 to build `el8` RPM package (#21655)
* Bump Python image to `3.10.3-alpine3.15` (#21688)
* Bump MSI embedded Python to 3.10.3 (#21746)

**RDBMS**

* Fix operations.py file installing dependencies in CloudShell (#21553)

**Role**

* [BREAKING CHANGE] `az ad sp create-for-rbac`: Stop defaulting `--scopes` to subscription (#21323)
* [BREAKING CHANGE] `az ad sp create-for-rbac`: When creating a self-signed certificate in keyvault, `validity_months` is changed from `years * 12 + 1` to `years * 12` (#21626)

**Service Bus**

* `az servicebus topic subscription rule create`: Add filter type parameter (#21629)

**Service Connector**

* `az webapp/spring-cloud connection create/update`: Provide `--service-endpoint` parameter to support vnet scenario (#21766)
* `az webapp/spring-cloud connection`: Add command `create redis/redis-enterprise` to support more target resources (#21763)

**SQL**

* [BREAKING CHANGE] `az sql db tde list-activity`: Command no longer exists (#21681)
* [BREAKING CHANGE] `az sql mi show/create/update/list`: Instead of `backupStorageRedundancy`, `currentBackupsStorageRedundancy` and `requestedBackupStorageRedundancy` properties are returned (#21681)
* `az command sql db str-policy set`: Make `diffbackup_hours` parameter optional (#21852)

**Storage**

* [BREAKING CHANGE] Fix #21494: `az storage blob upload/upload-batch`: Fix `--content-md5` for upload, ignore `--content-md5` for upload-batch (#21523)
* [BREAKING CHANGE] `az storage table/entity`: `--timeout` is removed for all sub commands (#21631)
* [BREAKING CHANGE] `az storage entity query/show`: `--accept` is removed (#21631)
* `az storage table/entity`: Add `--auth-mode login` to support RBAC (#21631)
* `az storage blob upload/upload-batch`: Make precondition work (#21603)
* `az storage blob upload-batch`: No longer exits on the first failure (#21603)
* Fix #21591: `az storage blob upload`: Fix storage blob upload not auto guessing file type (#21682)
* Fix `az storage entity merge`: Stop automatically casting DisplayVersion to float (#21240)
* `az storage blob download`: Support downloading managed disk with both SASUri and OAuth by specifying `--blob-url` with `--auth-mode login` (#21711)
* Fix #21699: `az storage blob upload-batch`: Fix upload-batch result url truncation issue (#21720)
* `az storage account\container\blob generate-sas`: Allow new permissions (#21767)

**Synapse**

* `az synapse role assignment list`: Fix showing only 100 results (#21600)
* `az synapse notebook import`: Fix `--folder-path` parameter problem (#21881)

2.34.1
++++++

**App Service**

* Hotfix: Fix #20489: `az webapp log tail`: Fix the AttributeError that 'NoneType' object has no attribute 'host_name_ssl_states' (#21398)
* Hotfix: Fix #20747: `az webapp create-remote-connection`: Fix the EOFError that ran out of input (#21398)
* Hotfix: Fix #20544: `az webapp config snapshot restore`: Fix the AttributeError that 'WebAppsOperations' object has no attribute 'restore_snapshot' (#21398)
* Hotfix: Fix #20011: `az webapp config ssl bind`: Fix the AttributeError that 'str' object has no attribute 'value' (#21398)
* Hotfix: Fix #19492: `az webapp config backup restore`: Fix the AttributeError that 'WebAppsOperations' object has no attribute 'restore' (#21398)

**Storage**

* [BREAKING CHANGE] `az storage blob upload/upload-batch`: Fix `--overwrite` that it no longer overwrite by default (#21485)

2.34.0
++++++

**ACR**

* `az acr manifest`: Add new command group to support managing artifact manifests in Azure Container Registries (#21161)
* Deprecate `az acr repository show-manifests` command and replace with `acr manifest metadata list` command (#21161)

**AKS**

* `az aks nodepool update`: Add `--node-taints` to allow modify node taints (#21138)
* `az aks get-credentials`: Add new parameter `--format` to support specifying the format of returned credential (#21383)
* `az aks nodepool`: Allow specifying `--scale-down-mode` in nodepool create and update (#21396)

**APIM**

* `az apim api import`: Update api-id description #18306 (#21248)
* Fix #21187: `az apim api create/update/import`: Fix header and query param names being swapped (#21202)

**App Config**

* `az appconfig kv import`: Add new parameter `--strict` to support strict import (#21067)

**App Service**

* [BREAKING CHANGE] `az webapp up`: Change supported runtimes (#21057)
* [BREAKING CHANGE] `az webapp create`: Change supported runtimes (#21057)
* [BREAKING CHANGE] `az webapp list-runtimes`: Add `--os`/`--os-type` argument, change runtimes, change default behavior to return both linux and windows stacks, and deprecate `--linux` argument (#21057)
* [BREAKING CHANGE] `az functionapp create`: Take runtime names and versions from API instead of hardcoded list (#21057)
* `az functionapp plan`: Update the max value of `--max-burst` to 100 (#21233)
* `az functionapp list-runtimes`: Add new command to show function app runtimes, versions, and compatible functions versions (#21057)
* `az webapp create`: Provide support `--https-only` flag (#21286)
* `az webapp deployment github-actions remove`: Fix the bug that path cannot start with a slash (#21392)

**ARM**

* `az account management-group entities`: Add a new command group to support entities (Management Groups and Subscriptions) operations for the authenticated user (#20942)
* `az account management-group hierarchy-settings`: Add a new command group to support operations on hierarchy settings defined at the management group level (#20942)
* `az account management-group tenant-backfill`: Add a new command group to support backfilling subscriptions for the tenant (#20942)
* `az account management-group subscription show`: Get the details of a given subscription under a given management group (#20942)
* `az account management-group subscription show-sub-under-mg`: Show what subscription is under a given management group (#20942)
* `az account management-group check-name-availability`: Check if a management group name is valid and available (#20942)
* `az deployment`: Fix the bug of 'bytes object has no attribute get' for error handling in retry cases (#21220)

**Backup**

* Add private endpoints support for Microsoft.RecoveryServices/vaults (#21097)

**Compute**

* `az vm create`: Fix the issue that VMCustomization is not enabled (#21232)
* `az vm disk attach`: Modify help description to guide how to use the `--ids` parameter correctly (#21300)
* `az restore-point`: Add new command group to support managing restore point (#19505)
* `az vmss create/update`: Add new parameters `--security-type`, `--enable-secure-boot` and `--enable-vtpm` to support Trusted Launch (#21354)
* `az vmss create/update`: Add new parameters `--automatic-repairs-action` to support repair action (#20485)
* `az vmss create/update`: Add new parameters `--v-cpus-available` and `--v-cpus-per-core` to support VMSize customization (#21368)

**Cosmos DB**

* `az managed-cassandra cluster update`: Fix to allow `--external-seed-nodes` and `--external-gossip-certificates` to be updated by the user (#21420)

**Eventhub**

* `az eventhubs namespace create`: Add `--user-assigned`, `--system-assigned`, `--encryption-config` (#21191)
* `az eventhubs namespace identity`: Cmdlets for event hubs identity (#21191)
* `az eventhubs namespace encryption`: Cmdlets for event hubs encryption (#21191)
* `az servicebus namespace create`: Add `--user-assigned`, `--system-assigned`, `--encryption-config` (#21270)
* `az servicebus namespace identity`: Cmdlets for event hubs identity (#21270)
* `az servicebus namespace encryption`: Cmdlets for event hubs encryption (#21270)

**IoT**

* `az iot hub create`: Add the `--enforce-data-residency` parameter to support creating resources with data residency enforced (and cross-region disaster recovery disabled) (#21348)
* `az iot dps create`: Add the `--enforce-data-residency` parameter to support creating resources with data residency enforced (and cross-region disaster recovery disabled) (#21348)

**Key Vault**

* Fix #21341: `az keyvault update`: Support updating tags (#21350)
* `az keyvault key create/import/set-attributes`: Support `--immutable` to mark release policy immutable (#21371)
* `az keyvault key import`: Support `--kty oct` to import AES key (#21380)

**Monitor**

* `az monitor log-analytics workspace table`: Add new command `create`, `delete` and `search-job create` to support Microsoft/Custom log/Search Results table operations (#20968)
* `az monitor log-analytics workspace update`: Add a new parameter `--data-collection-rule` to support update defaultDataCollectionRuleResourceId (#20968)
* `az monitor log-analytics workspace table`: Add new command `restore create` and `migrate` to support Restored logs table/migrate operations (#21340)

**Network**

* `az bastion ssh`: Provide support for Bastion SSH access on Darwin and Linux (#21171)
* `az network private-endpoint`: Associate IP configurations and ASGs when creating PE (#21284)

**Packaging**

* [BREAKING CHANGE] Drop Ubuntu 14.04 Trusty Tahr and Debian 8 Jessie support (#20869)
* [BREAKING CHANGE] Drop Ubuntu 21.04 Hirsute Hippo support (#21151)
* Add Ubuntu 21.10 Impish Indri support (#21151)
* Bump embedded Python to 3.8 for deb packages (#20869)

**Profile**

* [BREAKING CHANGE] `az account show`: Drop `--sdk-auth` (#21219)

**RDBMS**

* Fix bug for private dns zone provisioning to vnet resource group in different subscription (#21265)
* Enable rdbms-connect extension in Cloud Shell (#21294)

**Role**

* Add warning to `role` and `ad` commands about Microsoft Graph migration (#21302)

**SQL**

* `az sql server create/update`: Add federated client id support (#21293)

**Storage**

* `az storage account create/update`: Support `--sam-account-name` and `--account-type` (#21403)
* `az storage blob upload`: Add `--tier`, migrate to track2 (#21359)
* `az storage blob upload-batch`: Migrate to track2 (#21359)

2.33.1
++++++

**Compute**

* Hotfix: Fix #21224: Fix the issue that VMCustomization is not enabled (#21241)

**Packaging**

* [BREAKING CHANGE] Drop jmespath-terminal from docker image (#21277)

2.33.0
++++++

**ACR**

* `az acr connected-registry create`: Add `--notifications` to support adding patterns for generating notification events on connected registry artifacts (#20763)
* `az acr connected-registry update`: Add `--add-notifications` and `--remove-notifications` to support adding or removing patterns for generating notification events on connected registry artifacts (#20763)

**AKS**

* `az aks nodepool add/update/upgrade`: Add new parameter `--aks-custom-headers` to support custom headers (#21064)
* `az aks create`: Add new parameter `--snapshot-id` to support creating a nodepool from snapshot when creating a cluster (#21115)
* `az aks nodepool add/upgrade`: Add new parameter `--snapshot-id` to support creating a nodepool from snapshot (#21115)
* `az aks snapshot create/delete/list/show`: Add new commands to support the management of snapshot related operations (#21115)
* `az aks update/az aks nodepool update`: Allow empty string as label value

**App Config**

* [BREAKING CHANGE] Support app service slots (#20850)

**App Service**

* `az webapp vnet-integration add`: Fix a bug that prevented adding a vnet in a different subscription from the webapp (#20910)
* `az functionapp vnet-integration add`: Fix a bug that prevented adding a vnet in a different subscription from the functionapp (#20910)
* `az webapp create`: Support joining a vnet in a different subscription (#20910)
* `az functionapp create`: Support joining a vnet in a different subscription (#20910)
* `az functionapp create` : Remove preview from PowerShell runtime for linux (#20928)
* `az appservice plan update`: Add `--elastic-scale` and `--max-elastic-worker-count` parameters to support elastic scale (#20748)
* `az webapp update`: Add `--minimum-elastic-instance-count` and `--prewarmed-instance-count` parameters to support setting instance count (#20748)
* `az webapp up`: Add help text and debug text for configuration saving and loading (#20952)
* `az webapp list-runtimes`: Support node 16-lts runtime for linux and windows (#21055)

**Batch**

* `az batch create/activate`: Add clarify application package path help info for argument `--package-file` (#21000)

**Bot Service**

* `az bot create`: Add location as specified by user to bot creation for regionality/EUDB (#20716)

**Compute**

* `az image builder create`: Add new parameter `--proxy-vm-size` to support proxy VM size customization (#20904)
* `az image builder create`: Add new parameter `--build-vm-identities` to support user assigned identities customization (#20904)
* `az vmss update`: Add new parameter `--force-deletion` to support force delete VMSS (#20622)
* `az vm/vmss create`: Add warning log and modify help to inform that the default value `Contributor` of `--role` will be removed (#20924)
* `az disk-encryption-set create`: Make the parameter `--source-vault` un-required (#20256)
* `az vm create/update`: Add new parameters `--v-cpus-available` and `--v-cpus-per-core` to support VMSize customization (#20818)

**Cosmos DB**

* `az managed-cassandra cluster status`: Add table format support (#21131)

**Key Vault**

* `az keyvault create`: Add default permissions on keyvault creation (#20937)

**Monitor**

* `az monitor action-group`: Support event hub receiver (#21059)

**NetAppFiles**

* `az netappfiles account ad add`: Add new optional parameter named encrypt-dc-connections (#20919)
* `az netappfiles volume export-policy add`: Add missing optional parameters kerberos5_read_only, kerberos5_read_write, kerberos5i_read_only, kerberos5i_read_write, kerberos5_p_read_only, kerberos5_p_read_write, has_root_access, chown_mode (#20919)
* `az netappfiles account ad update`: Add command (#21043)

**Network**

* Add Microsoft.DataFactory/factories to supported Private Endpoints (#20895)
* Add Microsoft.Databricks/workspaces to supported private endpoints (#20992)
* `az network private-endpoint`: Add parameter and subgroup to support IP Configuration, ASG and NicName (#21039)
* `az network traffic-manager endpoint create/update`: Add new arguments `--min-child-ipv4` and `--min-child-ipv6`. (#21100)
* Add Microsoft.HybridCompute/privateLinkScopes to supported Private Endpoints (#21096)

**Packaging**

* Update Dockerfile base image from Alpine 3.14 to 3.15 (#21079)

**RDBMS**

* `az postgres flexible-server create`: Change default postgres version (#20922)

**Redis**

* `az redis create`: Add default value for identity and public network access as `None` (#21102)

**ServiceConnector**

* Support new target resources: servicebus, eventhub, appconfig (#21093)

**Storage**

* Stop supporting `--auth-mode login` for `az storage blob sync` and `az storage fs directory upload/download` (#20917)

2.32.0
++++++

**AKS**

* `az aks create`: Add new parameter `--enable-fips-image` to support enabling fips image (#20721)
* `az aks nodepool add`: Add new parameter `--enable-fips-image` to support enabling fips image (#20721)

**App Service**

* [BREAKING CHANGE] `az webapp up`: Remove support for the python|3.6 (linux and windows), ruby|2.5 (linux), and php|7.3 (windows) runtimes. Add support for the python|3.9 runtime (linux), php|8.0 (linux), and ruby|2.7 (linux) (#20770)
* [BREAKING CHANGE] `az webapp create`: Remove support for the python|3.6 (linux and windows), ruby|2.5 (linux), and php|7.3 (windows) runtimes. Add support for the python|3.9 runtime (linux), php|8.0 (linux), and ruby|2.7 (linux) (#20770)
* [BREAKING CHANGE] `az functionapp create`: Remove python 3.6 support (#20770)
* Fix #19550: `az staticwebapp users update`: Allow updating static web app user roles again (#20694)
* `az logicapp create`: Autogenerate a WS1 App Service Plan when no value for `--plan` or `--consumption-plan-location` is provided (#20678)
* `az appservice plan create`: Allow creating App Service Plans for Logic Apps (SKUs WS1, WS2, and WS3) (#20678)
* Fix #20757: `az webapp up`: Fix list index out of range when no `--plan` argument passed (#20760)
* Fix #18652: `az webapp up`: Search for \*.csproj in child directories (#20738)
* `az webapp list-runtimes`: Remove support for the python|3.6 (linux and windows), ruby|2.5 (linux), and php|7.3 (windows) runtimes. Add support for the python|3.9 runtime (linux), php|8.0 (linux), and ruby|2.7 (linux) (#20770)

**Backup**

* `az backup restore restore-azurewl`: Add client side validations (#20638)
* `az backup container unregister`: Support MAB type for parameter `--backup-management-type` (#20711)
* `az backup protectable-item list/show`: Add auto-protection policy and node-list field in the response for SQLInstance SQLAG (#20821)
* `az backup protection auto-enable-for-azurewl/auto-disable-for-azurewl`: Add support for SQLAG (#20821)

**Compute**

* `az vm/vmss create/update`: Expand validate license types for `--license-type` parameter (#20724)
* `az sig image-definition list-shared`: Add new parameters `--marker` and `--show-next-marker` to support paging (#20618)
* `az sig image-version list-shared`: Add new parameters `--marker` and `--show-next-marker` to support paging (#20618)

**IoT**

* `az iot hub update`: Add error handling for file-upload parameters and fixes empty $default storage endpoint errors (#20595)
* `az iot central app create`: Add new parameter `--mi-system-assigned` to support creating an app with system-assigned managed identity (#20448)
* `az iot central app identity show/assign/remove`: Add new commands to manage the system-assigned managed identity to an existing IoT Central app (#20448)
* `az iot dps access-policy`: Be replaced with `az iot dps policy` (#20682)
* `az iot dps linked-hub create`: Add convenience arguments for linking hubs (#20682)

**Network**

* Fix #19482: Azure Bastion AAD fix for new CLI core changes (#20648)
* `az network lb inbound-nat-pool create`: Add new parameter `--backend-pool-name` (#20835)

**Profile**

* `az account show/set`: Add `-n`, `--name` argument (#20777)

**Redis**

* `az redis identity`: Add support for assigning and modifying Identity (#20833)

**REST**

* [BREAKING CHANGE] `az rest`: Remove `resourceGroup`, `x509ThumbprintHex` transforms (#19579)

**Role**

* [BREAKING CHANGE] `az ad sp create-for-rbac`: Drop `name` property from the output. Use `appId` instead (#19808)
* [BREAKING CHANGE] `az ad sp create-for-rbac`: No role assignment will be created by default (#19805)

**Storage**

* `az storage copy`: Add positional argument `extra_options` to pass through options to `azcopy` (#20702)

**Synapse**

* [BREAKING CHANGE] `az synapse managed private endpoints create`: Remove `--resource-id` and `--group-id`, use `--file` instead (#20664)
* `az synapse sql pool create/restore`: Add parameters `--storage-type` to support specifying storage account type (#20553)
* `az synapse kql-script`: New command group to support Kusto script (#20699)

2.31.0
++++++

**AKS**

* `az aks update`: Support edit nodepool label after creation (#20187)
* `az aks nodepool update`: Support edit nodepool label after creation (#20187)
* `az aks create`: Fix issue that `--attach-acr` parameter can't work (#20406)

**AMS**

* Remove deprecated variable 'identifier_uri' from creating sp method (#20281)
* Update api version for AMS and AVA private link registration (#20266)

**App Service**

* `az functionapp create`: Add support for creating a webapp joined to a vnet (#20008)
* `az webapp up`: Fix failure to detect dotnet 6.0 web apps (#20157)
* `az appservice ase update`: Support for allowing new private endpoint connections on ASEv3 (#20084)
* `az appservice ase list-addresses`: Support ASEv3 (#20084)
* `az staticwebapp identity assign`: Assign managed service identity to the static web app (#20140)
* `az staticwebapp identity remove`: Disable static web app's managed service identity (#20140)
* `az staticwebapp identity show`: Display static web app's managed service identity (#20140)
* Fix #17507: `az staticwebapp functions`: Add support for linking existing function app to static webapp (bring your own functions) (#20116)
* `az staticwebapp create`: Update help text with guidance for repos in Github organizations (#20245)
* `az functionapp deployment source config-zip`: Fix #12289: Allow build on zip deploy for windows function apps (#20207)
* `az staticwebapp create`: Add better error message when attempting to create a static webapp that already exists (#20184)
* `az appservice`: Fix AttributeError during user error handling (#20264)
* `az appservice plan create`: Add `--zone-redundant` parameter to support enabling zone redundancy for high availability (#20302)
* `az webapp ssh`: Add proxy support (#20325)
* `az webapp create-remote-connection`: Add proxy support (#20325)
* `az webapp log download/tail`: Add proxy support (#20325)
* `az webapp create`: Fix container registry server url parsing for `--deployment-container-image-name/-i` argument (#20345)
* `az functionapp deployment source config-zip`: Fix returning success when the deployment did not succeed (#20261)
* `az staticwebapp appsettings set`: Make set functional (#18468)
* `az staticwebapp appsettings`: Switch to the new SWA app settings SDK methods (#20320)
* `az functionapp plan create`: Add `--zone-redundant` parameter to give the option to create a zone redundant app service plan (#20450)
* Support managed identity in App Service container (#20215)

**ARM**

* `az resource\group list`: Support querying data only by passing the tag name to `--tag` parameter (#20169)
* `az account management-group`: Add new parameters `--no-register` to skip RP registration for `Microsoft.Management` (#20166)
* `az deployment`: Prettify error output for ARM deployment (#20238)
* `az bicep install`: Add a new parameter `--target-platform/-t` to specify the running platform of Bicep CLI (#20250)
* `az bicep upgrade`: Add a new parameter `--target-platform/-t` to specify the running platform of Bicep CLI (#20250)
* `az deployment sub/tenant/mg create`: Fix the `KeyError: 'resourceGroup'` in outputting results in table format when deploying non-resource group level resources (#20455)
* `az policy assignment create` and `az policy assignment identity assign` support adding user assigned identity (#20480)
* `az bicep install`: Work now behind a corporate proxy (#20183)

**Backup**

* GA `az backup` and some bug fixes (#20291)
* `az backup protectable-item list/show`: Fix AttributeError for server_name (#20513)
* `az backup restore restore-disks`: Add support for Cross Zonal Restore (#20539)

**Cognitive Services**

* `az cognitiveservices account deployment`: Add new commands `show`, `list`, `create`, `delete` (#20551)
* `az cognitiveservices account commitment-plan`: Add new commands `show`, `list`, `create`, `delete` (#20551)
* `az cognitiveservices commitment-tier`: Add new command `list` (#20551)

**Compute**

* Fix #20182: `az snapshot create`: Fix auto-detection bug for `--copy-start` (#20190)
* Fix #20133: `az vm create`: Fix `--data-disk-delete-option` not working when no `--attach-data-disks` are provided (#20165)
* Fix boot diagnostics decoding (#16454)
* `az vm create/update`: Add new parameter `--enable-hibernation` to support enabling hibernation capability (#20235)
* `az vm/vmss run-command show`: Add new parameter `--instance-view` to support tracking the progress of RunCommand (#20191)
* Update the help description for unmanaged disks (#20394)
* `az disk create/update`: Add `--public-network-access` argument to control the policy for export on the disk (#20251)
* `az disk create/update`: Add `--accelerated-network` argument to support the accelerated networking (#20251)
* `az snapshot create/update`: Add `--public-network-access` argument to control the policy for export on the disk (#20251)
* `az snapshot create/update`: Add `--accelerated-network` argument support the accelerated networking (#20251)
* `az snapshot create`: Fix #20258: Fix creating a snapshot of a Uniform VMSS OS disk (#20306)

**EventGrid**

* GA `az eventgrid system-topic` (#20531)

**Key Vault**

* `az keyvault key encrypt/decrypt`: Support AES algorithm for MHSM (#20189)
* `az keyvault key rotation-policy update`: Support both camel case and snake case json for `--value` (#20530)

**NetAppFiles**

* `az netappfiles volume create`: Fix volume export policy (#20535)

**Network**

* `az network express-route peering connection ipv6-config`: Add new commands `set`, `remove` (#19887)
* `az network application-gateway waf-policy managed-rule exclusion`: Add new subgroup `rule-set` to support per rule exclusions (#20360)
* `az network bastion create`: Fix invalid validator when `--scale-units` is None (#20305)
* `az network vnet create`: Add `--enable-encryption` argument to support enable encryption on virtual network (#20355)
* `az network vnet update`: Add `--enable-encryption` argument to support enable encryption on virtual network (#20355)
* `az network vnet create`: Add `--encryption-enforcement-policy` argument to choose If Virtual Machine without encryption is allowed in encrypted Virtual Network. (#20355)
* `az network vnet update`: Add `--encryption-enforcement-policy` argument to choose If Virtual Machine without encryption is allowed in encrypted Virtual Network. (#20355)

**Packaging**

* Support Python 3.10 (#20195)
* Add Dockerfile.mariner to support Mariner build (#20061)

**Profile**

* `az logout`, `az account clear`: Remove ADAL token cache file `accessTokens.json` (#20308)

**RDBMS**

* Fix private DNS zone suffix bug (#20483)
* Fix #20124: `az mysql/postgres flexible-server db create`: Make resource group and server name required (#20162)
* `az postgres flexible-server`: Remove preview tag (#20426)

**Storage**

* `az storage share list-handle/close-handle`: New commands for share handle (#20144)
* GA account level and blob version level immutable storage (#20233)

**Synapse**

* [BREAKING CHANGE] `az synapse sql/pool audit-policy`: Remove `--blob-auditing-policy-name` (#20494)
* `az synapse notebook/spark-job-definition`: Add `--folder-path` argument (#20288)
* `az synapse spark pool create/update`: Add `--spark-config-file-path` (#20381)
* `az synapse spark job submit`: Fix for `--main-class-name` (#20537)
* `az synapse sql-script`: New command group to support sql script management (#20044)

2.30.0
++++++

**ACR**

* [BREAKING CHANGE] `az connected-registry`: `--repository` flag short version `-t` is being removed. (#19755)
* [BREAKING CHANGE] `az connected-registry install renew credentials`: Now it requires the user to confirm password generation. (#19755)
* `az connected-registry install`: Deprecate and redirect to `az acr connected-registry get-settings`. (#19755)
* `az connected-registry repo`: Deprecate and redirect to `az acr connected-registry permissions update`. (#19755)
* `az connected-registry permissions show`: A new command that allows the user to see the sync scope map information. (#19755)
* `az connected-registry get-settings`: A new command that retrieves the necessary information to install a connected registry and allows the generation of a new sync token password. (#19755)
* `az connected-registry create`: No longer adds a postfix to the sync token and scope map name. (#19755)

**AKS**

* `az aks create/update`: Add new parameter `--aks-custom-headers` to support for custom headers (#19807)
* `az aks create`: Support setting `--private-dns-zone` to none for private cluster creation (#19883)
* `az aks create/update`: Add new parameter `--enable-secret-rotation` and `--rotation-poll-interval` to support secret rotation (#19986)
* `az aks enable-addons`: Add new parameter `--enable-secret-rotation` and `--rotation-poll-interval` to support secret rotation (#19986)

**App Config**

* `az appconfig kv import/export`: Add new parameter `--profile` to support using `appconfig/kvset` profile (#19923)

**App Service**

* Fix #19617: `az webapp ssh`: Open Web SSH on the specified instance (#19769)
* `az staticwebapp hostname`: Support adding static webapp hostname via TXT validation (#20074)
* Enable support for PowerShell on Linux function apps with V4 (#19869)

**ARM**

* `az bicep publish`: Add new command to publish bicep modules (#19926)

**ARO**

* `az aro create`: Remove Identifier URIs (#20095)

**Compute**

* `az disk update`: Fix the problem that updating network access policy to `AllowPrivate` failed (#19862)
* `az vm update`: Add `--host` argument and `--host-group` argument to support assign an existing VM to a specific ADH (#19819)
* Fix #19599: `az vm create`: Fix the issue that `--nic-delete-option` not working when no `--nics` is provided. (#19861)
* `az snapshot create`: Support copyStart as createOption (#19875)
* `az vmss create/update`: Support in-guest patching for VMSS (#19961)
* `az vm application set/list`: Add new commands to support VM application (#19928)
* `az vmss application set/list`: Add new commands to support VMSS application (#19928)
* `az vm create`: Add `--ephemeral-os-disk-placement` argument to support choosing the Ephemeral OS disk provisioning location (#19886)
* `az vmss create`: Add `--ephemeral-os-disk-placement` argument to support choosing the Ephemeral OS disk provisioning location (#19886)
* `az vm update`: Add `--size` argument to support the resize (#20043)
* `az vmss update`: Add `--vm-sku` argument to support the resize (#20043)
* `az vm run-command`: Add new commands to support managing the running commands in VM (#19697)
* `az vm update`: Add `--ephemeral-os-disk-placement` argument to support choose the Ephemeral OS disk provisioning location (#20062)
* `az vmss update`: Add `--ephemeral-os-disk-placement` argument to support choose the Ephemeral OS disk provisioning location (#20062)
* `az sig gallery-application`: Add new commands to support managing gallery application (#19996)
* `az sig gallery-application version`: Add new commands to support managing gallery application version (#19996)
* GA the features related to Flex VMSS (#19994)

**Container**

* `az container create`: Add parameter `--zone` to support Availability Zone selection (#19895)
* `az container create`: Fix the issue that `--subnet` or `--vnet` cannot be used with IP address type `Public` to allow `Private` (#20032)
* `az container create`: Add Support for `--registry-login-server` to work with `--acr-identity` (#20055)

**Cosmos DB**

* `az cosmosdb mongodb retrieve-latest-backup-time`: Add new command for fetching latest restorable timestamp for Mongo Account. (#20007)
* `az cosmosdb locations`: Add new commands for listing account locations and their properties. (#20007)
* `az managed-cassandra cluster/data-center`: GA support for managed cassandra cluster and data center (#19962)

**DMS**

* `az dms project create/az dms project task create` : Add MySQL projects/tasks for offline migrations. (#19634)

**FunctionApp**

* [BREAKING CHANGE] `az functionapp devops-pipeline`: Remove commands and move them to `functionapp` extension (#19716)

**HDInsight**

* `az hdinsight create`: Add two parameters `--zones` and `--private-link-configurations` to support creating cluster with availability zones feature and creating private link enabled cluster with private link configurations feature. (#20060)

**Key Vault**

* Support Keyvault SKR (#19746)
* `az keyvault key random`: Request some random bytes from managedHSM (#19959)
* `az keyvault rotation-policy/key rotate`: Support rotate key and manage key rotation policy (#19927)
* `az keyvault create/update`: Add `--public-network-access` parameter (#19956)

**Monitor**

* `az monitor metrics alert condition` : Add support for 'skip metric validation' (#19907)

**NetAppFiles**

* [BREAKING CHANGE] `az netappfiles account backup-policy create/update`: Remove optional parameter `--yearly-backups`. (#19711)
* `az netappfiles account list`: Add option to skip `--resource-group` parameter and fetch accounts for subscription. (#19711)
* `az netappfiles pool create`: Add optional parameter named `--encryption-type` (#19711)
* `az netappfiles volume create`: Add optional parameters: `--network-features`, `--avs-data-store`, `--default-group-quota`, `--default-user-quota`, `--is-def-quota-enabled` (#19711)
* `az netappfiles volume update`: Add optional parameters: `--default-group-quota`, `--default-user-quota`, `--is-def-quota-enabled` (#19711)

**Network**

* `az network bastion create`: Add new parameter `--scale-units` and `--sku` to support setting scale unit (#19899)
* `az network vnet`: Add parameter `--bgp-community` (#19876)
* `az network private-endpoint-connection`: Support "Microsoft.Cache/Redis" (#19967)
* `az network private-endpoint-connection`: Support "Microsoft.SignalRService/WebPubSub" (#20042)

**RDBMS**

* Introduce MySQL georestore command and update validators (#19782)
* GA `az mysql flexible-server` (#19783)

**Service Bus**

* Fix MU capacity to include 16 when updating namespace (#19724)

**ServiceConnector**

* `az webapp/spring-cloud connection`: New command group to support service to service connection (#19834)

**SQL**

* `az sql server ad-admin`: Fix breaking change made to update and delete (#19866)

**Synapse**

* `az synapse kusto`: Add Kusto pool(mgmt) support (#19984)

2.29.1
++++++

**Compute**

Hotfix: Fix #19897,#19903: Fix static webapp commands that are broken due to the upgrade of `azure-mgmt-web` to 4.0.0 (#19897)

2.29.0
++++++

**AKS**

* `az aks check-acr`: Bump canipull to 0.0.3 alpha to support sovereign cloud (#19616)
* `az aks create/update`: Add new parameter `--disable-local-accounts` to support disable local accounts (#19680)
* `az aks enable-addons`: Support open-service-mesh addon (#19574)
* `az aks create/update`: Add support for updating tags (#19709)

**App Config**

* Fix dependencies for multiple installations of `jsondiff` and `javaproperties` (#19792)

**App Service**

* `az webapp create/up`: Correct the typo of wrong java version in help (#19532)
* `az logicapp create/delete/show/list`: Add new commands to support logicapp related operations (#19472)
* `az staticwebapp environment delete`: Add command to support deleting static app environment (#19514)
* `az functionapp show`: Add kind validation for show operation (#19493)
* `az webapp config backup list`: Fix issue that returned backup configuration instead of backup list (#19722)
* `az logicapp start/restart/stop`: Add new commands for logicapp (#19613)
* `az webapp config storage-account`: Update parameter descriptions (#19646)

**ARM**

* `az deployment`: Remove the log of printing request body from custom policy (#19445)
* `az deployment group create`: Fix incorrect scope in the example of creating deployment from template-spec (#19563)
* `az ts create`: Simplify overwrite confirmation message (#19790)

**Backup**

* `az backup container register`: Fix refresh container bug (#19570)
* `az backup`: Add CRR functionality for Azure Workload (#19664)
* `az backup`: Add support for MAB backup management type in some sub commands (#19710)

**Compute**

* `az sig create/update`: Add new parameter `--soft-delete` to support soft delete (#19569)
* `az sig image-version`: Add new parameter `--replication-mode` to support setting replication mode (#19580)
* `az vm/vmss update`: Fix disassociation VM/VMSS from capacity reservation (#19666)
* `az vm/vmss create`: Hide alias `--data-delete-option` in help (#19728)
* `az vmss create`: Support quick creation for flexible VMSS (#19712)

**Container**

* [BREAKING CHANGE] `az container create`: Remove `--network-profile` parameter, property no longer supported (#19705)
* `az container logs`: Fix the attribute error introduced by Track 2 migration (#19637)
* `az container create`: Add parameter `--acr-identity` for support of MSI authenticated ACR image pull (#19705)

**Cosmos DB**

* `az cosmosdb identity assign/remove`: Add support for user identity (#19533)

**Eventhub**

* `az eventhubs namespace update`: Add `--infra-encryption` for encryption (enable-require-infrastructure-encryption). (#19677)
* `az eventhubs namespace create/update`: Add `--disable-local-auth` to enable or disable SAS authentication. (#19677)
* `az eventhubs namespace`: Add `private-endpoint-connection` and `private-link-resource` command groups (#19677)

**Key Vault**

* [BREAKING CHANGE] Fix #18479: `az keyvault network-rule add`: Fix the bug which allows duplicate `--ip-address` with the ones already in the network-rule (#19477)
* Fix #10254: `az keyvault network-rule add`: Add capability to accept multiple ip-addresses as a list in the form of `--ip-address ip1 [ip2] [ip3]...` (#19477)
* `az keyvault delete`: Add warning when deleting managed HSM (#19515)

**Network**

* Add `az network custom-ip prefix wait` (#19474)
* Add `az network vnet-gateway packet-capture wait` (#19474)
* Add `az network vnet-gateway vpn-client ipsec-policy wait` (#19474)
* Add `az network vnet-gateway nat-rule wait` (#19474)
* Add `az network vpn-connection packet-capture wait` (#19474)
* Private link and endpoint support for provider `Microsoft.BotService/botServices` to supported private endpoints operations (#19555)
* `az network application-gateway client-cert`: Add commands `update` and `show` (#19466)
* `az network application-gateway ssl-profile`: Add commands `update` and `show` (#19466)
* `az network application-gateway http-listener create`: Add parameter `--ssl-profile` (#19466)
* `az network application-gateway http-listener update`: Add parameter `--ssl-profile` (#19466)
* Onboard hdinsight private link2 network cmdlets (#19676)
* `az network bastion create`: Add `--tags` argument (#19693)
* Private link and endpoint support for provider `Microsoft.Authorization/resourceManagementPrivateLinks` (#19742)
* Private link and endpoint support for provider `Microsoft.MachineLearningServices/workspaces` (#19729)

**Profile**

* `az account show`: Deprecate `--sdk-auth` (#19414)

**RDBMS**

* [BREAKING CHANGE] `az postgres flexible-server migration`: Change `--properties @{filepath}` to `--properties {filepath}` (#19516)
* `az postgres flexible-server migration create`: User can pass in filename with double quotes or no quotes and same for absolute paths. (#19516)
* `az postgres flexible-server migration check-name-availability`: Add a command to check if a migration name is available. (#19516)
* `az postgres flexible-server migration update`:  Add `--start-data-migration` to reschedule the migration to start right now. (#19516)
* Update list-skus, create command location setting and replica command (#19531)

**Role**

* `az ad sp create-for-rbac`: Deprecate `--sdk-auth` (#19414)

**Security**

* Add command `az security setting update` (#19561)

**Storage**

* Fix #19279: Add clarification for file system name to also mean container name. (#19481)
* Fix #19059: Fix doc link to point to public doc website (#19484)
* `az storage account hns-migration start/stop`: Support migrate a storage account to enable hierarchical namespace (#19520)
* `az storage container-rm create/update`: Add `--root-squash` to support enable nfsv3 root squash or all squash (#19549)
* Fix #17858: `az storage blob upload`: make --name optional (#19553)
* `az storage account create/update`: Add --public-network-access parameter (#19576)
* `az storage container immutability-policy create`: Add --allow-protected-append-writes-all/--w-all parameter (#19698)
* `az storage container legal-hold set`: Add --allow-protected-append-writes-all/--w-all parameter (#19698)
* `az storage account create/update`: Enable account level immutability (#19662)

**Synapse**

* [BREAKING CHANGE] `az synapse sql/pool audit-policy update`: Add parameter `blob-storage-target-state`, `log-analytics-target-state`, `event-hub-target-state` (at least choose one of these 3 paras)  (#19384)
* `az synapse integration-runtime`: Support start/stop integration-runtime (#19524)
* `az synapse trigger`: Add az synapse trigger wait (#19524)
* `az synapse trigger-run`: Add az synapse trigger-run cancel (#19524)
* `az synapse integration-runtime`: Deprecate `create` command and will redirect to `managed create` or `self-hosted create` command (#19524)
* `az synapse dataset/pipeline/linked-service/trigger`: Deprecate `set` command and will redirect to `update` command (#19524)
* `az synapse workspace-package`: Support workspace package CRUD (#19560)
* `az synapse spark pool update`: Support add or remove specific packages (#19560)
* `az synapse workspace create/update`: Add arguments for supporting synapse workspace repository configuration (#19643)
* `az synapse spark-job-definition`: Support spark job definition CRUD (#19593)

2.28.1
++++++

**ARM**

Hotfix: Fix #19468: pip installs azure-cli 2.0.73 because of the dependency on deprecated package `jsmin` (#19495)

2.28.0
++++++

**ACR**

* `az acr create/update`: Add support for disabling export through `--allow-exports` (#19065)
* `az acr`: Bump core api-version to `2021-06-01-preview` from `2020-11-01-preview`. agent_pool, tasks and runs operations unchanged from `2019-06-01-preview` (#19065)
* `az acr task credential`: Fix the issue where task credentials were not used (#19241)
* `az acr task logs`: Fix the AttributeError when querying the task logs (#19366)

**ACS**

* [BREAKING CHANGE] `az aks nodepool update`: Change rejecting the ability to use max-surge with node-image-only (#19295)

**AKS**

* `az aks install-cli`: Add support for kubelogin darwin/arm64 releases (#19072)
* Fix incorrectly passed parameter for option `--assign-kubelet-identity` in aks create sub-command (#19157)
* Upgrade api-version to `2021-07-01` for ACS module (#19245)
* `az aks create/update`: Add support for private cluster public fqdn feature (#19302)
* Revert PR #18825: `az aks create/update`: Add parameter `--auto-upgrade-channel` to support auto upgrade (with fix) (#19297)
* `aks create/aks nodepool add`: Add parameter ` --os-sku` to support choosing the underlying container host OS (#19374)

**App Config**

* `appconfig kv import/export`: Add endpoint validation during import and export (#19145)

**App Service**

* `az webapp config storage-account list/add/update/delete`: Remove preview flag (#19177)
* Fix #18497: `functionapp identity show`: Fix the crashes when the functionapp name does not reference an existing functionapp (#19127)
* `az webapp config set`: Add additional help examples for powershell users (#19185)
* Fix #17818: `az functionapp update`:  Add instance validation for updating functionapp (#19141)
* `az webapp config hostname add`: Fix the issue caused by AttributeError (#19188)
* `az webapp config hostname add`: Fix the issue caused by AttributeError (#19348)
* Fix #16470: `az staticwebapp secrets`: Add commands to manage deployment secrets (#19347)
* `az webapp deployment source config-local-git`: Fix the issue caused by AttributeError when slot option is specified (#19404)
* `az webapp deleted restore`: Fix the issue that 'WebAppsOperations' object has no attribute 'restore_from_deleted_app' (#19404)
* `az webapp up`: Add ability to deploy Linux and Windows webapps to the same resource group (#19344)
* `az webapp up`: Add support for deploying to an App Service Environment (#19425)
* Fix #19098: `az webapp deployment slot auto-swap `: Fix the AttributeError error for parameters `--slot --disable` (#19376)

**ARM**

* `az feature registration`: Add az feature registration apis (#19146)
* `az tag create`: Add the note for handling existing tag in help (#19057)
* `az ts create`: Fix issue where creating a template spec with inner deployments that reference a common template fails (#19312)

**CDN**

* `az cdn endpoint create`: Fix endpoint creation failure with `--content-types-to-compress` (#19401)

**Compute**

* `az ssh vm`: Raise error for managed identity and Cloud Shell (#19051)
* Upgrade api-version for VM and VMSS from `2021-03-01` to `2021-04-01` (#19158)
* `az vmss create/update`: Support spot restore policy to VM scale sets (#19189)
* Add new examples for creating disk from share image gallery (#19270)
* `az vm image list/list-offers/list-skus/list-publishers/show`: Add new parameter `--edge-zone` to support querying the image under edge zone (#19206)
* Fix the issue caused by the lack of `os_type` when creating VM from shared gallery id (#19291)
* Update shared image gallery doc (#19427)
* `az capacity reservation`: Add new commands to manage capacity reservation (#19416)
* `az capacity reservation group`: Add new commands to manage capacity reservation group (#19416)
* `az vm create/update`: Add new parameter `--capacity-reservation-group` to support association to capacity reservation (#19416)
* `az vmss create/update`: Add new parameter `--capacity-reservation-group` to support association to capacity reservation (#19416)
* `az vmss create`: Support creating VMSS from shared gallery image (#19417)

**IoT**

* `az iot hub/dps certificate update/create`: Add `--verified` argument to mark certificates as verified without proof-of-possession flow (#19363)
* `az iot hub create/update`: Add `--disable-local-auth`, `--disable-device-sas`, and `--disable-module-sas` arguments to configure accepted SAS key authentication methods. (#19363)

**Key Vault**

* `az keyvault private-endpoint-connection list`: Support list mhsm's private endpoint connections (#19163)
* `az keyvault set-policy`: `--key-permissions` add new option `release` (#19411)

**Network**

* Fix NSG rule creation example mistake (#19242)
* Add a new command group `az network custom-ip prefix`. (#19218)
* `az network public-ip`: Add parameter `--ip-address`. (#19218)
* `az network public-ip prefix create`: Add parameter `--custom-ip-prefix-name`. (#19218)
* `az network dns record-set {record-type} add-record`: Support idempotent (#19237)
* PrivateLink supports `Microsoft.Purview/accounts` 2021-07-01 (#19338)
* `az network bastion ssh`: connect to a Virtual machine through ssh using Bastion Tunneling. (#19240)
* `az network bastion rdp`: connect to a Virtual machine through native RDP using Bastion Tunneling. (#19240)
* `az network bastion tunnel`: connect to a Virtual machine using Bastion Tunneling. (#19240)

**Packaging**

* Use Python 3.9 in Homebrew formula (#19222)
* When installed with RPM, run python3.6 if available (#19110)
* Add Ubuntu 21.04 Hirsute Hippo support (#19367)
* Add Debian 11 Bullseye support (#19370)
* Drop Ubuntu 20.10 Groovy Gorilla support (#19368)

**PowerBI**

* Add private link provider Microsoft.PowerBI/privateLinkServicesForPowerBI (#19204)

**RDBMS**

* [BREAKING CHANGE] `az postgres flexible-server migration`: Rename `--migration-id` to `--migration-name` (#19149)
* [BREAKING CHANGE] `az mysql flexible-server create/update`: `--high-availability` available parameter is changed from 'Enabled' to 'ZoneRedundant' and 'SameZone' . (#19301)
* Fix maintenance window update issue with MySQL and Change restart parameter to be case insensitive (#19231)
* `az mysql flexible-server restore` enables network option change from private network  to public network and vice versa. (#19301)
* `az mysql flexible-server replica create`: Add `zone` parameter. (#19301)

**Role**

* `az role assignment create`: Support `ForeignGroup` for `--assignee-principal-type` (#19132)
* `az role assignment create`: Do not invoke Graph API if `--assignee-principal-type` is provided (#19219)

**SQL**

* `az sql mi update`: Add --subnet and --vnet-name parameters to support the cross subnet update SLO (#18886)
* Fix the enum name change in track2 Python SDK (#19142)

**Storage**

* Fix #10765: Refine error message when account key is incorrect padding (#13965)

**Synapse**

* [BREAKING CHANGE] Rename `az synapse workspace key update` to `az synapse workspace key activate` and remove `--is-active` (#19304)
* Optimize submit spark job arguments (#19038)
* `az synapse`: Add managed private endpoints feature. (#19117)
* Spark pool remove library requirement (#19358)

2.27.2
++++++

**Cosmos DB**

* Hotfix: `az cosmosdb restore`: Fix the restore command for deleted accounts (#19273)

2.27.1
++++++

**ARM**

* Hotfix: Fix #19124: `az deployment what-if`: Handle unsupported and no effect change types (#19144)

**Batch**

Upgrade batch data-plane to [azure-batch 11.0.0](https://pypi.org/project/azure-batch/) (#19100)
Upgrade batch management-plane to [azure-batch-mgmt 16.0.0](https://pypi.org/project/azure-mgmt-batch/16.0.0/) (#19100)
`az batch location`: Add `list-skus` command to list SKUs available in a location (#19100)
`az batch account`: Add `outbound-endpoints` command to list outbound network dependencies (#19100)

2.27.0
++++++

**ACR**

* [BREAKING CHANGE] `az acr connected-registry install info`: Add a new required parameter `--parent-protocol`. (#18954)
* [BREAKING CHANGE] `az acr connected-registry install renew-credentials`: Add a new required parameter `--parent-protocol`. (#18954)
* `az acr import`: Support new parameter `--no-wait` (#18572)
* Fix the Python SDK compatibility issue when migrating Track 2 (#18786)
* `az acr build`: Make file .dockerignore include directories with `!` (#18821)

**AKS**

* `az aks check-acr`: Fix issues parsing certain client minor versions (#18727)

**AppConfig**

* [BREAKING CHANGE] `appconfig feature set`: Set the value of parameter `--description` to empty string if it is not specified (#18907)
* [BREAKING CHANGE] `az appconfig feature`: Support namespacing for feature flags and change output fields (#18990)
* `az appconfig create`: Add tags support when creating resource (#18783)

**App Service**

* `az webapp config set`: Add support for VNet Route All property. (#18460)
* `az webapp vnet-integration add`: Default to VNet Route All. Allow cross subscription integration. (#18460)
* `az appservice ase create`: Support for ASEv3 External and Zone redundancy (#18748)
* `az webapp hybrid-connection add`: Improve help/error message and unblock Linux (#18843)
* `az webapp config access-restriction remove`: Fix #18947 issue removing service endpoint rules (#18986)
* Fix #17424: `az appservice plan show`: Provide correct exit status (#18994)

**ARM**

* `az what-if`: Fix output formatting (#18721)
* `az bicep uninstall`: Add new command to uninstall bicep (#18744)
* `az bicep build`: Fix an issue where running with --stdout doesn't print any output (#18744)
* `az provider register`: Add deprecate info for `--accept-term` (#18739)
* `az lock create/delete`: Add examples for operating different levels of locks (#18890)
* `az deployment group/sub/mg/tenant create`: Add --what-if parameter for invoking What-If with the deployment create commands. (#18924)
* `az deployment group/sub/mg/tenant create`: Add --proceed-if-no-change parameter to skip confirmation when --confirm-with-what-if is set and there's no changes in What-If results. (#18924)
* Bump api-version from 2020-10-01 to 2021-04-01 (#18923)
* `az ts create`: Make parameter `--template-file` support bicep file (#18888)
* `az resource create`: Add example for creating site extension to web app (#18935)
* `az ts export`: Fix the issue that export template specs with no linked templates failed (#18928)

**Backup**

* `az backup vault`: Add support for Customer Managed Keys(CMK) (#18733)
* `az backup restore restore-disks`: Add MSI usage in IaaS VM Restore (#18961)

**CDN**

* `az cdn endpoint rule`: Add OriginGroupOverride action support (#18711)

**Compute**

* `az sig image-version create`: Support mixing disks, snapshots, and vhd (#18741)
* `az vmss update`: Upgrade package version to fix securityProfile issue (#18788)
* `az vm boot-diagnostics get-boot-log`: Fix crash when getting boot diagnostics log (#18830)
* `az vm list-skus`: Fix the issue that it can't query the SKU which with partially zones available (#18939)
* `az vm auto-shutdown`: Fix the issue that `--webhook` is required when `--email` is passed in (#18958)
* `az vm create`: Support creating VM from shared gallery image (#19037)
* `az vm secret add`: Add note to use Azure Key Vault VM extension instead in help (#19045)

**Container**

* `az container exec`: Fix and improve terminal experience (#18909)

**DataBoxEdge**

* Migrate databoxedge to track2 SDK (#18678)

**DMS**

* `az dms project create/az dms project task create`: Remove MySQL projects/tasks for online migrations since they are no longer supported. (#18709)

**IoT**

* `az iot hub create/update`: Add checks to prevent bad file-upload identity parameters when hub doesn't have identity (#18966)
* `az iot hub create/update`: Add `--fileupload-notification-lock-duration` parameter (#18966)
* `az iot hub create/update`: Deprecate `fileupload-storage-container-uri` parameter (#18966)
* `az iot dps/hub certificate create`: Certificates will now always be uploaded in base64 encoding. (#18966)

**Key Vault**

* [BREAKING CHANGE] Fix #13752: az keyvault create not idempotent. Creating existing keyvault will fail. (#18520)
* Fix #6372: table output for secrets isn't correct (#18308)

**Maps**

* `az maps creator create`: Support maps creator create managed (#18450)
* `az maps creator update`: Support maps creator update managed (#18450)
* `az maps creator list`: Support maps creator list managed (#18450)
* `az maps creator show`: Support maps creator show managed (#18450)
* `az maps creator delete`: Support maps creator delete managed (#18450)

**NetAppFiles**

* `az netappfiles volume pool-change`: Update help description for pool-change (#18835)

**Network**

* `az network application-gateway create`: Add `--ssl-certificate-name` argument (#18861)
* Private link add Microsoft.ServiceBus/namespaces provider (#18999)
* `az network application-gateway waf-policy custom-rule match-condition add`: Add examples (#18957)
* `az network express-route port link update`: Add `--macsec-sci-state` argument. (#18814)
* Private link add Microsoft.Web/hostingEnvironments provider (#19025)
* `az network lb frontend-ip update`: Support cross tenant for argument `--gateway-lb`. (#18792)
* `az network nic ip-config update`: Support cross tenant for argument `--gateway-lb`. (#18792)
* Private link add Microsoft.StorageSync/storageSyncServices provider (#19000)
* Private link add Microsoft.Media/mediaservices provider (#18997)
* Private link add Microsoft.Batch/batchAccounts provider (#18970)

**Packaging**

* Add licenses to all Python packages (#18749)
* Add SOCKS Proxy Support (#18931)

**PolicyInsights**

* Migrate to track 2 SDK (#18740)

**RDBMS**

* PostgreSQL, MySQL migration to GA API (#18921)

**Redis**

* `az redis create\update`: Add new parameter `--redis-version` (#18996)

**SQL**

* Update Microsoft.Sql to track2 SDK (#18637)
* `az sql server outbound-firewall-rule create`: Azure CLI Commands for Outbound Firewall Rules (#18671)

**Storage**

* Fix #18352: `az storage fs file list --exclude-dir` breaks with `--show-next-marker` (#18816)
* `az storage fs generate-sas`:  Support generate sas token for file system in ADLS Gen2 account (#18768)
* `az storage account blob-service-properties`: Support last access tracking policy (#18731)
* `storage container-rm migrate-vlw`: Support Version level Worm (VLW) (#18540)
* `az storage copy` add new option `--cap-mbps` (#18344)

**Synapse**

* `synapse workspace key update`: Fix the issue that updating a workspace key failure due to parameter `--is-active-cmk` lost (#18719)
* Reimport notebook failure (#18718)

2.26.1
++++++

**ACR**

* Hotfix: `az acr build\connected-registry\pack\run\scope-map`: Fix the compatibility bug caused by SDK upgrade (#18853)

**AKS**

* Hotfix: `az aks create`: Fix the issue that `assign-kubelet-identity` option can't work (#18795)

**Storage**

* Hotfix: Fix issue caused by jwt upgrade. (#18811)
* Hotfix: `az storage fs directory download`: Fix the issue with `--sas-token` to generate valid sas url (#18811)
* Hotfix: `az storage blob copy start`: Fix the issue in copy from different account (#18730)

2.26.0
++++++

**AKS**

* Migrate ACS module to track 2 SDK (#18117)
* Upgrade api-version to 2021-05-01 for ACS module (#18593)
* Add UltraSSD support (#18649)
* Support use custom kubelet identity (#18615)
* `az aks get-credentials`: Add a check for KUBECONFIG environmental variable (#18704)

**APIM**

* Add version parameter for apim api import (#18604)
* Fix apim upgrade bug when specifying protocols (#18605)
* `az apim create`: Fix `--enable-managed-identity` true failure (#18554)

**App Config**

* Stop overwriting KeyVault reference content type during import (#18602)

**App Service**

* [BREAKING CHANGE] `az functionapp create`: Remove support for EOL Node 8 and 10 (#18676)
* [BREAKING CHANGE] `az webapp deployment source config`: Remove vsts-cd-manager (#18203)
* [BREAKING CHANGE] `az functionapp deployment source config`: Remove vsts-cd-manager (#18203)
* `az webapp/functionapp config access-restriction add`: Prevent duplicate rules using service endpoints. (#18024)
* `az webapp/functionapp config access-restriction remove`: Remove service endpoints are case-insensitive (#18024)
* `az webapp config access-restrictions add`: Skip validation if user does not have access to get service tag list. (#18527)
* Add support for Linux Consumption and improve how content share name is generated. (#18675)
* Fix an issue where adding VNET integration & Hybrid connections on a slot is not working (#18582)
* `az appservice domain create`: Fix get correct domain agreements (#18622)
* `az webapp deployment github-actions add/remove`: new commands (#18261)

**AppConfiguration**

* Add support for `disable_local_auth` (#18619)

**ARM**

* `az provider register`: Make parameter `--accept-term` become not required (#18509)

**ARO**

* `az aro create`: Add cidr values for pod/service (#18457)
* Fail if resource doesn't exist on delete (#18546)

**Azurestack**

* Azure Stack Hub Support for AKS and ACR has been added in 2020-09-01-hybrid profile (#18118)

**Backup**

* `az backup container`: Fix container registration
Workload container registration fix, SDK upgraded to 0.12.0, Fixed and Re-ran tests (#18592)
* Add Archive Support for Azure CLI (#18535)

**Billing**

* Migrate billing to track2 SDK (#18608)

**Cognitive Services**

* `az cognitiveservices account`: Add list-deleted, show-deleted, recover, purge commands (#18464)

**Compute**

* `az sig create/update`: Add --permissions to specify the permission of sharing gallery. (#18503)
* `az sig share`: Manage gallery sharing profile. (#18503)
* `az sig list-shared`:  List shared galleries by subscription id or tenant id. (#18503)
* `az sig show-shared`:  Get a shared gallery. (#18503)
* `az sig image-definition list-shared`:  List shared galleries by subscription id or tenant id. (#18503)
* `az sig image-definition show-shared`:  Get a shared gallery image. (#18503)
* `az sig image-version list-shared`:  List shared galleries by subscription id or tenant id. (#18503)
* `az sig image-version show-shared`:   Get a shared gallery image version. (#18503)
* `az vmss create`: Support NetworkApiVersion for Vmss with OrchestraionMode == Flexible (#18132)
* Make dependent resources of VM/VMSS support edge zone (#18708)
* Update from CoreOS to Flatcar (#18644)
* Add the hint to suggest users use the standard public IP when creating VM (#18662)

**Container Registry**

* Migrate to track2 SDK (#18611)

**Cosmos DB**

* Add point-in-time restore commands to the stable branch. (#18568)
* Add support for selecting Cosmos DB analytical storage schema type (#18636)

**HDInsight**

* `az hdinsight create`: Remove the incoming breaking change notice for the parameter `--workernode-size` and `--headnode-size`. (#18519)
* Add three new cmdlets to support new azure monitor feature: (#18519)

**NetAppFiles**

* `az netappfiles account ad add`: Optional parameter added named --administrators (#18666)
* `az netappfiles pool create`: Optional parameter added --cool-access (#18666)
* `az netappfiles volume create`: Optional parameters added named --chown-mode, --cool-access, --coolness-period, --coolness-period (#18666)
* `az netappfiles volume backup restore-status`: Command added to see backup restore status (#18666)

**Network**

* `az network routeserver create`: Add `--public-ip-address` argument. (#18663)

**RDBMS**

* Add autogrow parameter for MySQL and add database name to output json when created (#18441)

**Resource**

* Third-party S2S Consent/Permission Enumeration (#18433)

**Security**

* Remove preview from security module (#18529)

**SQL**

* Bump sdk version (#18373)
* Fix for server create in SQL 0.28 (#18640)
* `az sql db ledger-digest-uploads`:  Support SQL Ledger (#18672)
* Fix for IdentityType for UMI (#18693)
* `az sql db str-policy set/show`: Add Set and Show ShortTermRetentionPolicy (#14919)

**Storage**

* GA support secured SMB (#18638)
* `az storage account create`: Support `--enable-nfs-v3` to set NFS 3.0 protocol (#16766)
* Support container soft delete (#18508)

2.25.0
++++++

**ACR**

* `az acr connected-registry`: Minor bug fixes (#18288)

**App Service**

* `az webapp deployment source config-local-git`:  Fix to set SiteConfig (#18364)

**ARM**

* `az resource tag`: Fix the problem of tagging resources with resource type `Microsoft.Network/publicIPAddresses` (#18254)
* `az policy assignment non-compliance-message`: New command group for policy assignment non-compliance messages (#18158)
* `az policy assignment update`: New command for partially updating existing policy assignments (#18158)

**Backup**

* Migrate backup to track2 SDK (#17831)

**Compute**

* Upgrade api-version for VM and VMSS from '2020-12-01' to '2021-03-01' (#18233)
* `az vm create`: Support delete option for NICs and Disks for VMs in Azure CLI (#18238)
* Support user_data for VM and VM Scale Sets (#18432)

**Container**

* `az container exec`: Decode received bytes as utf-8 string (#18384)

**EventGrid**

* Migrate track2 SDK (#18210)

**HDInsight**

* Migrate to track2 Python SDK 7.0.0 (#18237)

**Iot Hub**

* Fix for user-assigned identity ARM issue on remove (#18205)

**Key Vault**

* Fix #11871: AKV10032: Invalid issuer error for operations in non-default tenant/subscription (#18162)
* `az keyvault set-policy/delete-policy`: Support --application-id (#18209)
* `az keyvault recover`: Support MHSM (#18150)
* `az keyvault private-link-resource list`: Support MHSM (#18273)
* `az keyvault private-endpoint-connection`: Support MHSM (#18273)

**NetAppFiles**

* `az netappfiles volume backup status`: Command added to get the status of the backup for a volume. (#18303)
* `az netappfiles volume update`: Optional parameter added named `--snapshot-policy-id` o assign a snapshot policy to the volume. (#18303)
* `az netappfiles volume backup create`: Optional parameter added named `--use-existing-snapshot` to manually backup an already existing snapshot. (#18303)
* `az netappfiles volume backup update`: Optional parameters added named `--use-existing-snapshot` to manually backup an already existing snapshot. Optional parameter label also added to add a label to backup. (#18303)

**Network**

* Support `Microsoft.Sql/servers` provider in Private link (#18268)
* `az network private-link-resource list`: Support `--type microsoft.keyvault/managedHSMs` (#18273)
* `az network private-endpoint-connection`: Support `--type microsoft.keyvault/managedHSMs` (#18273)

**RDBMS**

* Add commands for Github actions (#17949)
* `az postgres flexible-server migration`: Add customer facing feature to migrate postgres db servers from Sterling to Meru platform (#18161)
* Private DNS zone parameter added for restore command, high availability validator (#18218)
* Change server default location (issue reported) (#18157)

**Role**

* [BREAKING CHANGE] `az ad sp create-for-rbac`: `--name` is now only used as the `displayName` of the app. It is not used to generate `identifierUris` anymore. `name` in the output is now the same as `appID` (`servicePrincipalNames`) and deprecated. (#18312)

**SignalR**

* `az signalr identity`: Add managed identity related command (#18309)
* `az signalr cors update`: Add update command for cors (#18309)

**Storage**

* `az storage blob copy start`: Support --tier and --rehydrate-priority (#18170)
* GA release storage file share NFS and SMB multichannel (#18232)
* [BREAKING CHANGE] `az storage account create`: Remove `StorageFileDataSmbShareOwner` option for --default-share-permission (#18396)
* `az storage blob list`: --delimiter parameter value will now be honored (#18394)

**Synapse**

* Update to AZ Synapse mgmt 2.0.0 (#18195)
* Spark configuration conversion, which cause the failure (#18328)

**Webapp**

* Add to `az webapp deploy` param help text (#17743)

2.24.2
++++++

**Container**

* Hotfix: Fix #18276: `az container create` fails with `AttributeError: 'ResourcesOperations' object has no attribute 'create_or_update'`

2.24.1
++++++

**App Service**

* Hotfix: Fix #18266 - webapp config appsettings set command causing all values to default to "false"

**ARM**
* Hotfix: Fix deserialization issue in the What-If formatter of ARM template

**Compute**
* Hotfix: Fix the bad request issue when creating VMSS in Azure Stack

**IoT**
* Hotfix: Fix issue for removing last user-assigned identity from IoT Hub

2.24.0
++++++

**AKS**

* `az aks check-acr`: Add the nodeslector linux to avoid the "canipull" pod to be scheduled on the windows node (#17933)
* Sdk update (#18031)
* az aks create and update azure-rbac (#18026)
* Add run-command cli (#18051)

**App Config**

* Allow importing key-values with unicode characters from file (#17990)

**App Service**

* [BREAKING CHANGE] `az webapp list-runtimes`: Add Dotnet6 support and update runtimes (#17967)
* `webapp log tail`: Fix #17987: logging.warning call with invalid 'end' argument (#17988)
* Fix #16838- az cli update app setting command always making slotsetting to true (#17895)
* `az appservice`: Add function to retrieve users github personal access token (#17826)
* az staticwebapp appsettings set issue #17792 (#18034)
* Fix #18033: az staticwebapp appsettings set of missing positional param app_settings (#18043)
* Fix issues with APIs signature that changed with Track2 update (#18082)
* Fix get resource management client properly (#18142)
* Add interactive way to get token for staticwebapp (#18083)
* Fix an issue where assign and remove identities would fail with a call to NoneType (#18084)

**ARM**

* Migrate resource to track2 SDK (#17783)
* `az ts`: Add UiFormDefinition file support to TemplateSpecs for GA (05/04) (#17869)

**ARO**

* Add cluster credential rotation (#17925)

**Compute**

* `az sshkey create`: Save private key to local file system (#18022)

**Cosmos DB**

* Create and manage Role Definitions and Role Assignments for enforcing data plane RBAC on Cosmos DB SQL accounts (#18091)

**DevTestLabs**

* `az labs create environment`: Fix error creating an environment from an ARM template (#17959)

**HDInsight**

* [BREAKING CHANGE] `az hdinsight create`: Use getting default sku api to set workernode and headnode size if customer does not provide. (#17552)

**IoT**

* `az iot hub create`: Support assigning identities and assigning roles to system-managed identity. (#18098)
* `az iot hub update`: New parameter `--file-upload-storage-identity` to allow for managed-identity authenticated file upload. (#18098)
* `az iot hub identity assign`: New command to assign user/system-assigned managed identities to an IoT Hub. (#18098)
* `az iot hub identity show`: New command to show identity property of an IoT Hub. (#18098)
* `az iot hub identity show`: New command to update identity type of an IoT Hub. (#18098)
* `az iot hub identity remove`: New command to remove user/system-assigned managed identities from an IoT Hub. (#18098)
* `az iot hub routing-endpoint create`: New `--identity` parameter allows choosing a user/system-assigned identity for routing endpoints. (#18098)
* `az iot hub route create`: New routing source-type `DeviceConnectionStateEvents` (#18098)

**Kusto**

* Update command group long summary (#18107)

**Network**

* Bump api version from '2020-11-01' to '2021-02-01' (#18104)
* New command group `az network lb address-pool tunnel-interface` (#18136)
* `az network lb frontend-ip update`: New parameter `--gateway-lb` (#18136)
* `az network nic ip-config update`: New parameter `--gateway-lb` (#18136)
* `az network rule create/update`: New parameter `--backend-pools-name` (#18136)
* `az network vnet-gateway create`: Add new parameter `--nat-rule` (#18045)
* Add new cmd group `az network vnet-gateway nat-rule` (#18045)
* `az network vpn-connection create`: Add new parameter `--ingress-nat-rule` and `--egress-nat-rule` (#18045)
* `az network vnet create`: Add new parameter `--flowtimeout` (#18032)

**Packaging**

* Support Python 3.9 (#17368)

**RDBMS**

* Change IOPS logic for MySQL (#17974)
* Prevent private DNS zone track2 migration breaking rdbms module (#18062)

**Service Fabric**

* [BREAKING CHANGE] `az sf cluster certificate`: Remove all commands under this group. Please follow the instructions here to add/remove cluster certificates: https://docs.microsoft.com/en-us/azure/service-fabric/service-fabric-cluster-security-update-certs-azure#add-a-secondary-certificate-using-azure-resource-manager. (#18056)
* [BREAKING CHANGE] `az sf managed-service update`: Remove deprecated parameter --drop-source-replica-on-move. (#18056)
* [BREAKING CHANGE] `az sf managed-service create`: Remove deprecated parameters --service-dns-name, --drop-source-replica-on-move and -instance-close-delay-duration. (#18056)
* [BREAKING CHANGE] `az sf cluster`: Rename parameter --vault-resource-group to --vault-rg. (#18056)
* `az sf managed-cluster and sf managed-node-type`: Set groups as not preview (#18056)
* Update azure-mgmt-servicefabricmanagedclusters package to the latest version 1.0.0 that uses 2021-05-01 GA api version. (#18056)
* `az sf managed-cluster create`: Add parameters --upgrade-mode, --upgrade-cadence and --code-version. (#18056)
* `az sf managed-node-type`: Add parameters --data-disk-type, --is-stateless and --multiple-placement-groups. (#18056)

**SQL**

* `az sql server create`: Add a space to split the concatenated words in the help message of the argument --assign-identity. (#17966)
* `az sql server update`: Add a space to split the concatenated words in the help message of the argument --assign_identity. (#17966)

**Storage**

* [BREAKING CHANGE] `az storage share-rm delete`: Raise error when there are snapshots for target file share and add `--include` to specify deleting target file share and its snapshots (#18088)
* `az storage blob generate-sas`: Add spaces to split the concatenated words in the help message of the arguments --cache-control, --content-disposition, --content-encoding, --content-language and --content-type. (#17940)
* `az storage blob url`: Add a space to split the concatenated words in the help message of the argument --snapshot. (#17940)
* `az storage container generate-sas`: Add spaces to split the concatenated words in the help message of the arguments --cache-control, --content-disposition, --content-encoding, --content-language and --content-type. (#17940)
* Upgrade storage API version to 2021-04-01 (#18064)
* Support default share permission (#16462)
* Support cross tenant object replication (#18063)
* GA blob inventory (#18046)
* `az storage share-rm list`: Support list with snapshots. (#18088)

2.23.0
++++++

**ACR**

* `az acr check-health`: Add support to verify dns routings to private endpoints (#17746)
* Fix #17618: Update credential add/update handling for tasks created using --auth-mode (#17715)

**AKS**

* `az aks update`: Add `--windows-admin-password` to support updating Windows password (#17684)
* `az aks update`: Support updating from SPN cluster to MSI cluster. (#17902)
* `az aks create`: Add `--enable-encryption-at-host` parameter (#17813)

**App Service**

* [BREAKING CHANGE] Update websites SDK to the latest version (azure-mgmt-web==2.0.0) & Adopt track2 SDK (#17146)
* [BREAKING CHANGE] Rename `az staticwebapp browse` to `az staticwebapp show` (#17870)
* Add option of sku for `az staticwebapp create --sku` (#17870)
* Add command `az staticwebapp update` (#17870)
* `az webapp/functionapp config access-restriction add/remove`: Support for Service Tag, Http headers and multi-source rules. (#17687)

**ARM**

* `az bicep`: Replace datetime APIs that are not available in Python 3.6 (#17675)
* `az deployment group create`: Fix the compatibility issue of api-version for parameter `--template-specs` (#17896)

**Backup**

* `az backup vault create`: Add tags as an optional argument (#17735)
* Make AFS configure backup flow idempotent (#17839)

**CDN**

* `az cdn endpoint rule add`: Fix delivery rule creation for non-Microsoft SKU (#17822)

**Compute**

* Extended location for Compute RP (#17522)
* `az sig image-version create`: Support creating from a VHD (#16371)
* `az vm create --count`: Support vnet and subnet configuration (#17660)
* `az vmss extension upgrade`: Fix a bug (#17711)
* Add error message for `vm identity assign` (#17685)
* Zone-redundant storage (ZRS) managed disks (#17754)
* `az disk create`: Trusted launch (#17775)
* `az disk create`: Hibernation (#17775)
* Fix a compatibility issue of old API version (#17906)
* `az sig image version create`: Support data disk VHDs (#17706)

**Feedback**

* Do not minify feedback issue body (#17353)

**FunctionApp**

* Fix issue with zip deploy where local time was provided but UTC was expected (#17722)
* Update stacks api json to add PowerShell on Linux in Functions (#17678)

**HDInsight**

* Add Incoming BREAKING CHANGE for removing default value of `--workernode-size` and  `--headnode-size` (#17862)

**Key Vault**

* [BREAKING CHANGE] Support soft-delete feature for managed-HSM. `keyvault delete --hsm-name` will perform soft delete on a MHSM. (#17834)

**Marketplace Ordering**

* New command group `az term` to accept/show terms (#17686)

**Misc.**

* Define theme for Cloud Shell (#17283)

**Monitor**

* New command `az monitor metrics list-namespaces` (#17472)

**Network**

* [BREAKING CHANGE] az network dns record-set a show: Property `arecords` in output will be changed to `aRecords`. (#17787)
* New command `az network express-route list-route-tables-summary`. (#17450)
* New command `az network express-route peering get-stats`. (#17450)
* New command `az network express-route peering connection list`. (#17450)
* `az network lb create`: Add new parameter `--edge-zone` (#17623)
* `az network nic create`: Add new parameter `--edge-zone` (#17623)
* `az network private-endpoint create`: Add new parameter `--edge-zone` (#17623)
* `az network private-link-service create`: Add new parameter `--edge-zone` (#17623)
* `az network public-ip create`: Add new parameter `--edge-zone` (#17623)
* `az network public-ip prefix create`: Add new parameter `--edge-zone` (#17623)
* `az network vnet create`: Add new parameter `--edge-zone` (#17623)
* New Command `az network lb list-nic` (#17729)
* `az network application-gateway show-backend-health`: support probe operation arguments. (#17753)
* `az network vpn-connection list`: support parameter `--vnet-gateway`. (#17664)
* New command `az network vnet-gateway disconnect-vpn-connections`. (#17664)
* New command `az network vnet-gateway vpn-client show-health`. (#17664)
* New command `az network vnet-gateway vpn-client ipsec-policy show`. (#17664)
* New command `az network vnet-gateway vpn-client ipsec-policy set`. (#17664)
* New command `az network vnet-gateway packet-capture start`. (#17664)
* New command `az network vnet-gateway packet-capture stop`. (#17664)
* New command `az network vnet-gateway show-supported-devices`. (#17664)
* New command `az network vpn-connection list-ike-sas`. (#17664)
* New command `az network vpn-connection packet-capture start`. (#17664)
* New command `az network vpn-connection packet-capture stop`. (#17664)
* New command `az network vpn-connection show-device-config-script`. (#17664)
* `az network private-link-resource list`: support more providers for `--type` (#17731)

**Packaging**

* Bump python to `3.8.9` in docker image (#17840)
* Bump bundled python to `3.8.9` in MSI. (#17816)

**Role**

* `az role assignment create/update`: Auto complete `assignee_principal_type` (#17669)

**SQL**

* `az sql db create`: Add --ha-replicas argument (#17636)
* `az sql db replica create`: Add --ha-replicas argument (#17636)
* Allow short mw policy names for mi (#17703)

**SQL VM**

* Make SqlServerLicenseType as optional (#17766)

**Storage**

* Fix #16272 & #16853: Refine error message (#17630)
* `az storage account create`: Add edge zone support (#17528)
* Support user assigned identity for storage account (#16613)
* `az storage account create/update`: Support sas&key policy (#17815)

**Synapse**

* `az synapse notebook create`: Create a notebook (#17867)

2.22.1
++++++

**ARM**

* Hotfix: Fix the issue that bicep build broken in Python 3.6

**Key Vault**

* Hotfix: GA for managed-HSM related commands and parameters

2.22.0
++++++

**ACR**

* [BREAKING CHANGE] `az acr connected-registry install info`: Replace keys ACR_REGISTRY_NAME, ACR_SYNC_TOKEN_NAME, ACR_SYNC_TOKEN_PASSWORD, ACR_PARENT_GATEWAY_ENDPOINT, and ACR_PARENT_PROTOCOL with a new connected string key, ACR_REGISTRY_CONNECTION_STRING. (#17152)
* [BREAKING CHANGE] `az acr connected-registry install renew-credentials`: Replace keys ACR_REGISTRY_NAME, ACR_SYNC_TOKEN_NAME, ACR_SYNC_TOKEN_PASSWORD, ACR_PARENT_GATEWAY_ENDPOINT, and ACR_PARENT_PROTOCOL with a new connected string key, ACR_REGISTRY_CONNECTION_STRING. (#17152)
* `az acr connected-registry create`: Verify before the creation of the token and sync scope map that all ancestors are active. (#17566)
* `az acr connected-registry create`: Add the repository and gateway permissions required for creation to all the ancestors of the new connected registry if needed prior to the connected registry creation. (#17566)
* `az acr connected-registry delete`: Remove the gateway permissions of the deleted resources from all its ancestors' sync scope maps. (#17566)
* `az acr connected-registry repo`: New command to add repository permissions to a connected registry and all its ancestors' sync scope maps, and remove repository permissions from the connected registry and all its descendants' sync scope maps (#17566)

**AKS**

* `az aks create`: Add support for `--private-dns-zone` and `--fqdn-subdomain` feature (#17430)

**App Config**

* Configure max line width for YAML parser to stop wrapping output (#17401)
* Fix bug in print preview of restore command (#17344)

**App Service**

* Fix #17219: Fix ssl bind bug (#17479)
* Remove preview flag for Python 3.9 in create function app command (#17546)
* Bugfix: Handle if only single publish profile is returned (#17495)
* Fix #16203: az webapp log tail supports webapps running on Linux. (#17294)

**ARM**

* [BREAKING CHANGE] `az bicep build`: Change the parameter `--files` to `--file` (#17547)
* [BREAKING CHANGE] `az bicep decompile`: Change the parameter `--files` to `--file` (#17547)
* Fix #17379: bicep auto install results in invalid json output from deployment (#17380)
* `az bicep build`: Add a parameter `--outdir` for specifying the output directory (#17547)
* `az bicep build`: Add a parameter `--outfile` for specifying the output file path (#17547)
* Fix an issue where checking version upgrade for Bicep CLI throws exception if GitHub API rate limit is hit (#17547)
* `az policy exemption`: Add new commands to support policy exemption (#17565)

**Backup**

* Fix #14776: Fix `--force` parameter functionality for `az backup vault delete` command (#16957)
* Fix on demand backup (#17367)
* `az backup protectable-item list`: Add optional parameter `--backup-management-type` (#17414)
* Fix policy create with rgNamePrefix and rgNameSuffix (#17571)
* `az backup protectable-item list`: Add `--server-name` as an optional argument (#17614)

**Compute**

* `az ssh vm`: Support VM SSH with Service Principal (#17554)
* Add VMSS Rolling Upgrade opt (#17580)
* New command: `vm install-patches` (#17549)
* Disk encryption set: Add `--enable-auto-key-rotation` (#17577)

**Container**

* Fix #16499: `az container create`: Fix handling of return value from network_profiles.create_or_update (#17486)

**Cosmos DB**

* Support for managed service identity & default identity (#17583)

**EventGrid**

* `az eventgrid system-topic create/update`: Add MSI Support (#17361)
* `az eventgrid [partner topic | system-topic] event-subscription`: Add support for StorageQueueMessageTTL, AdvancedFilters, EnableAdvancedFilteringOnArrays (#17440)
* `az eventgrid [partner topic | system-topic] event-subscription`: Add support for delivery attribute (#17496)
* `az eventgrid topic create`: Add support for creating topic for azure or azurearc (#17496)

**Interactive**

* Fix #16931: Fix `KeyError` in `az interactive --update` (#17389)

**NetAppFiles**

* `az netappfiles account ad add`: Optional parameter added named allow-local-ldap-users (#17370)
* `az netappfiles volume create`: Optional parameter added named ldap-enabled (#17370)
* `az netappfiles volume backup status show`: Operation added (#17370)
* Update backup tests (#17492)

**Network**

* `az network vnet-gateway`: `--vpn-auth-type` allow multi value (#17505)

**Packaging**

* [BREAKING CHANGE] RPM installed az now uses `python3` instead of hard-coded `/usr/bin/python3`. (#17491)

**RDBMS**

* Allow DB server private access from different subscription (#17502)
* Modify server create with private network, fix restore time bug (#17570)

**Search**

* `az search service create`: Add async (--no-wait) options. (#17446)
* `az search service update`: Add async (--no-wait) options. (#17446)
* `az search shared-private-link-resource create`: Add async (--no-wait) options. (#17446)
* `az search shared-private-link-resource update`: Add async (--no-wait) options. (#17446)

**Service Fabric**

* Add managed application cli commands (#17404)

**Storage**

* `az storage fs directory upload/download`: Support adls gen2 file system directory upload&download (#17292)
* `az storage fs file list`: Support --show-next-marker (#17408)
* `az storage share-rm`: Support create/show/delete snapshots (#17449)

**Synapse**

* [BREAKING CHANGE] `az synapse role assignment create`: Role names at old version are not allowed, Sql Admin, Apache Spark Admin, Workspace Admin (#17476)
* [BREAKING CHANGE] `az synapse role assignment create`: When --assignee argument can't  uniquely determine the principal object, the command will raise error instead of adding a role assignment for the uncertain principal object. (#17476)
* `az synapse role scope list`:  List all scopes synapse supports. (#17476)
* `az synapse role assignment create/list/delete`: Add --scope/--item-type/--item arguments to support manage role assignments based on scope. (#17476)
* `az synapse role assignment create/list/delete`: Add --assignee-object-id argument, it will bypass Graph API and uniquely determine principal object instead of deducing principal object using --assignee argument. (#17476)

2.21.0
++++++

**ACR**

* Output a trace in `az acr login` for self-diagnosing potential docker command latency (#17115)
* Fix #17172: When run check-health behind corporate proxy (#17177)
* `acr update`: Support anonymous pull (#17006)
* Fix #16700: Use "exists" api to check storage blob existence (#17299)

**AKS**

* `aks update`: Add `--no-uptime-sla` (#17192)
* Fix cross-sub assigning identity error and attach acr error (#17281)
* Add support for node public IP prefix ID (#17138)

**APIM**

* [BREAKING CHANGE] `apim backup`: `--storage-account-container` not support multi-value. (#17315)
* [BREAKING CHANGE] `apim restore`: `--storage-account-container` not support multi-value. (#17315)

**App Service**

* [BREAKING CHANGE] Fix #16087: `az webapp config ssl create`: set `--name` parameter as required. (#17079)
* Fix #17053: `az webapp show` return null values for SiteConfig properties (#17054)
* Fix #17207: `az webapp log config`: 'level' always defaults to verbose (#17259)

**ARM**

* `az bicep build`: fix an issue where build warnings are not shown (#17180)

**Backup**

* Add `id_part` for sub-resource names to fix `--ids` (#17165)
* Fix #17094: Created separate test suite for CRR tests (#17183)
* `az backup protection check-vm`: Add `--vm` and `--resource-group` as optional params (#16974)

**Cache**

* GA `az cache` (#17264)

**CDN**

* `az afd rule create`: Fix `--help` message (#17282)

**Compute**

* Fix a Windows vm user update bug (#17257)
* Fix #16585: `az vmss deallocate`: `--instance-ids` failed (#17274)
* `az vm create`: New parameter `--platform-fault-domain` in FLEX VMSS mode (#16409)
* `az vm create`: `--patch-mode` for Linux VM (#16409)
* `az ssh vm`: Automatically launch browser when getting certificate fails (#17093)
* `az vm create`: New parameter `--count` (#17217)
* `az vm create`: Trusted Launch (#17354)
* Fix #16037: az vm open-port accepts list of ports (#17255)

**Extension**

* Add actionable message when an extension is not compatible with the CLI core (#16751)

**Key Vault**

* `az keyvault role definition list`: Support `--custom-role-only` to list only custom role definitions (#17119)
* Support keyvault custom role definition (#17109)
* Add `--no-wait` for command `az keyvault security-domain download` and `--target-operation` for command `az keyvault security-domain wait` (#17263)

**NetAppFiles**

* `az netappfiles account backup show`: Operation added. (#17173)
* `az netappfiles account backup delete`: Operation added. (#17173)
* `az netappfiles account ad add`: Parameter `--ldap-over-tls` added. (#17173)
* `az netappfiles account create`: Parameter `--encryption` added. (#17173)
* `az netappfiles account update`: Parameter `--encryption` added. (#17173)
* `az netappfiles volume create`: Parameter `--encryption-key-source` added. (#17173)
* `az netappfiles volume create`: Default export policy removed for nfsv4.1 and optional parameters added for setting up an export policy for nfsv4.1: rule_index, unix_read_only, unix_read_write, cifs, allowed_clients (#17173)

**Network**

* `az network public-ip prefix create`: Support `--zone 1 2 3` (#17279)
* `az network lb frontend-ip create`: Support `--zone 1 2 3` (#17279)
* Bump version from '2020-08-01' to '2020-11-01' (#17290)
* `az network lb address-pool`: Support subnet when creating or updating an IP-based backend pool of a load balancer. (#17336)

**RDBMS**

* Added tests for flexible server team pipeline (#16947)
* Python SDK migration (#17191)
* Added PostgreSQL database create, show, and delete feature (#17271)
* Updating Python SDK to 8.1.0b2 (#17359)

**Role**

* `az ad app permission list/grant`: Refine error message when no associated Service Principal exists for the App (#17051)

**Search**

* `az search`: GA (#17258)

**Service Fabric**

* `az sf certificate`: deprecate cluster cert commands. (#17190)

**SQL**

* Add Server Trust Group commands (#17275)

**Storage**

* Fix #16917: `az storage account generate-sas` fails if a connection string is provided (#17200)
* Fix #16979: `az storage container create` fails when providing storage container metadata (#17202)

**Upgrade**

* Fix #16952: Fix ImportError after upgrade (#17314)

**Misc.**

* Allow configuring theme (#17073)

2.20.0
++++++

**AKS**

* Add support for SGX addon 'confcom' (#16869)

**AMS**

* Update module to use 2020 Azure Media Services api. (#16492)
* `az ams account encryption`: New subgroup to show or set the encryption for the media service account (#16492)
* `az ams account storage set-authentication`: New command to set the authentication for the storage account associated with the media service account (#16492)
* `az ams account create (mi-system-assigned)`: New `--mi-system-assigned` parameter for account create to set the managed identity of the media account (#16492)
* `az ams account mru set`: This command will no longer work for Media Services accounts that are created with the 2020-05-01 version of the API or later. (#16492)
* `az ams live-event create (stretch-mode, key-frame-interval, transcrip-lang, use-static-hostname, custom hostname)`: Add new parameter options to live-event create command (#16492)
* `az ams live-event standby`: New command to put the live event in standby mode (#16492)
* `az ams transform create (videoanalysismode, audioanalysis mode)`: New parameter options for transform create (#16492)

**App Service**

* `az webapp config ssl bind`: handle if webapp and appservice plan in different rg. Also reference text updates (#16778)
* Fix #8743: az webapp deploy (#16715)
* Bugfix: Add generateRandomAppNames.json to setup (#17035)
* `az functionapp create`: Add preview support for creating dotnet-isolated apps. (#17066)
* Fix #12150: Support for subnet ID in vnet-integration add (#16902)
* `az functionapp create`: Remove preview flag from Node.js 14. (#16877)

**ARM**

* `az deployment group/sub/mg/tenant validate/create/what-if`: Add support for Bicep files (#16857)
* `az bicep install`: New command for installing Bicep CLI (#16857)
* `az bicep upgrade`: New command for upgrading Bicep CLI (#16857)
* `az bicep build`: New command for building Bicep files (#16857)
* `az bicep version`: New command for showing the current installed version of Bicep CLI (#16857)
* `az bicep list-versions`: New command for showing the available Bicep CLI versions (#16857)
* `az managedapp definition update`: Add new command for updating managedapp definition (#16966)

**Backup**

* `az backup recoverypoint show-log-chain`: Add start/end time in show-log-chain table output (#16753)
* BugFix: Enable Alternate Location Restore for SQL/SAPHANA protected items (#16997)

**CDN**

* Add cli support for AFD SKU (#16951)

**Compute**

* `az vm (extension) image list`: Make it more robust (#16992)
* `az vmss create`: Fix a license type issue (#17007)
* Upgrade API version to 2020-12-01 (#17042)
* `az vm create`: add `--enable-hotpatching` (#17042)

**Cosmos DB**

* Upgrade to version 3.0.0 and add support for NetworkAclBypass + Update Mongo ServerVersion + backup policy (#17021)

**Extension**

* Support config of extension index url (#15128)

**IoT Central**

* `az iot central app`: Address several S360 fixes (#17022)
* `az iot central app update`: Remove the need of checking etag when updating the existing iotc app. (#17022)
* Change the resourceType (IotApps) to be in camel case. (#17022)

**Key Vault**

* [BREAKING CHANGE] `az keyvault role assignment/definition list`: `roleDefinitionName` should be `roleName` in command output (#16781)
* [BREAKING CHANGE] `id` changes to be `jobId`, `azureStorageBlobContainerUri` changes to be `folderUrl` in command output of `az keyvault backup/restore`, `az keyvault key restore` (#17011)

**Network**

* Bump version from '2020-07-01' to '2020-08-01' (#16889)
* `az network public-ip create`: Support `--zone 1 2 3` after '2020-08-01' (#17043)
* `az network routeserver peering`: Rename `--vrouter-name` by `--routeserver` (#17049)
* `az network express-route peering create`: Support ipv6 address (#17048)
* `az network public-ip create`: Expose a new argument `--tier` (#17069)

**OpenShift**

* Update of `az openshift` deprecation warning (#16604)

**Search**

* `az search`: Fix the `--identity-type` helper's guide. (#17039)

**SQL**

* Update `az sql mi` examples (#16852)
* `az sql db/elastic-pool create/update`: Add `maintenance-configuration` argument (#16915)
* `az sql db replica create`: Add `--secondary-type` argument (#16960)

**Storage**

* [BREAKING CHANGE] `az storage account file-service-properties`: Default to enable delete retention policy with retention days 7 in server side (#17028)
* Fix #16872: az storage blob now (2.19) requires login even if connection-string is provided (#16885)
* Fix #16959: az storage copy crashes: ValidationError: local variable 'service' referenced before assignment (#16971)
* Fix #14054: 'NoneType' object has no attribute '__name__' (#16993)
* Fix #16679: `az storage blob download` fails with "Permission denied" if the destination file is a directory (#17008)
* Upgrade storage api version to 2021-01-01 (#17028)
* Support version in Lifecyle management policy (#16724)
* Support storage account shared key access management (#16759)
* `az storage account network-rule`: GA resource access rules (#16995)
* Support double encryption for encryption scope (#17087)
* `az storage account blob-service-properties update`: Support --change-feed-retention-days (#16990)
* Support rewrite existing blob (#16796)

2.19.1
++++++

**Key Vault**

* Hotfix: Dependency package `azure-keyvault-administration` is pinned to 4.0.0b1

2.19.0
++++++

**ACR**

* `az acr connected-registry install info`: Add new key `ACR_SYNC_TOKEN_NAME` with the same value as `ACR_SYNC_TOKEN_USERNAME`. A warning that the latter will be deprecated is displayed. (#16561)
* `az acr connected-registry install renew-credentials`: Add new key `ACR_SYNC_TOKEN_NAME` with the same value as `ACR_SYNC_TOKEN_USERNAME`. A warning that the latter will be deprecated is displayed. (#16561)

**AKS**

* Add managed cluster stop/start bindings (#16599)
* `az aks check-acr`: Fix Kubernetes version check (#16718)

**APIM**

* GA the command group (#16811)

**App Config**

* [BREAKING CHANGE] `az appconfig feature filter add`: Support adding JSON objects as feature filter parameter values (#16536)

**App Service**

* `az appservice ase/plan`: Support ASEv3 (#16516)
* Fix #16026 and #16118 for az appservice plan (#16516)
* Fix #16509: Add support for os-preference (#16575)
* Improve behavior of appservice ase create-inbound-services to allow skipping DNS services and support DNS for ASEv2 (#16575)
* `az webapp up/az webapp create`: Fix nonetype errors (#16605)
* `az webapp up/create`: better error handling of app name with period (#16623)
* Fix #16681: `az webapp config ssl import`: Fix bug that causes failures on national clouds (#16701)

**ARM**

* `az provider register`: Support registering management group (#15847)

**Backup**

* Add CRR functionality for IaaSVM and other CRR commands (#16557)
* `az backup protectable-item list`: Add protectable-item-type as an optional argument (#16765)

**BotService**

* `az bot create/update`: Add Encryption features `--cmk-key-url` and `--encryption-off` (#16694)
* `az bot update`: Rename Encryption-OFF arg to CMK-OFF and updating api version (#16794)

**Compute**

* [BREAKING CHANGE] vmss create: Rename orchestration mode values (#16726)
* New command group sshkey. Allow referencing a SSH key resource when creating a VM (#16331)
* `az disk create/update`: Add parameter `--enable-bursting` to support disk bursting (#16702)

**Extension**

* Support extension command prefix match for dynamic install (#16254)

**HDInsight**

* `az hdinsight create`: Add a new parameter `--enable-compute-isolation` to support create cluster with compute isolation feature. (#16752)

**Key Vault**

* `az keyvault key import`: Support `--curve` parameter for importing BYOK keys (#16593)
* `az keyvault certificate download`: Fix deprecated/removed method call (#16319)
* `az keyvault create/update`: Remove preview tag for `--enable-rbac-authorization` (#16630)

**Monitor**

* `az monitor metrics alert create`: Fix 'resource is not found' error (#16741)

**NetAppFiles**

* `az netappfiles account ad add`: Add parameter `--security-operators`. (#16467)
* `az netappfiles volume create`: Add parameter `--smb-continuously-available`. (#16467)
* `az netappfiles volume create`: Add parameter `--smb-encryption`. (#16467)
* `az netappfiles`: No longer in preview mode. (#16467)

**Network**

* [BREAKING CHANGE] `az network vrouter`: Deprecate this command group, please use `az network routeserver`. (#16494)
* `az network routeserver`: Add new command group. (#16494)
* `az network application-gateway create`: Add parameter `--ssl-profile-id` (#16762)
* `az network application-gateway client-cert`: Manage trusted client certificate of application gateway (#16762)
* `az network application-gateway ssl-profile`: Manage ssl profiles of application gateway (#16762)
* Add support for private endpoint connections to DigitalTwins (#16668)

**Profile**

* `az login`: Launch browser in WSL 2 (#16556)

**RDBMS**

* `az mysql flexible-server create --iops`: Allow user to choose IOPS for their SKU. (#15831)
* Update Postgres restore command to support available zone (#16693)

**Search**

* Upgrade to use the latest (8.0.0) azure-mgmt-search python sdk (#16707)

**Security**

* Add new commands for `az security` (#16398)

**SQL**

* Add managed hsm regex match to SQL (#15109)
* Upgrade azure-mgmt-sql to 0.26.0 (#16618)
* `az sql mi create/update`: Add support for maintenance configuration in managed instance operations (#16229)
* Support SQL server DevOps audit policy commands (#16595)

**Storage**

* Fix #16079: public blob gives error (#16578)
* GA Storage routing reference (#16550)
* Fix #9158: Cannot generate a working SAS key from a policy (#16549)
* Fix #16489: Upgrade azcopy to 10.8.0 (#16552)
* `az storage account blob-service-properties`: Support default service version (#16682)
* Fix #16519: azcopy is given more powerful SAS than needed (has write, only needs read) (#16731)

**Synapse**

* `az synapse workspace create `: Add parameter `--key-identifier` to support to create workspace using customer-managed key. (#16224)
* `az synapse workspace key`: Add CRUD cmdlets to support to manage keys under specified synapse workspace. (#16224)
* `az synapse workspace managed-identity`: Add cmdlets to support CRUD managed identity to sql access setting. (#16224)
* `az synapse workspace`: Add data exfiltration protection support, add parameter `--allowed-tenant-ids`. (#16224)

2.18.0
++++++

**ACR**

* `az acr create / update`: Add `--allow-trusted-services`. This parameter determines whether trusted azure services are allowed to access network restricted registries. The default is to allow. (#16530)

**AKS**

* `az aks check-acr`: Add new check-acr command (#16490)

**App Service**

* Fix #13907: `az webapp config ssl import`: Change command to also import App Service Certificate (#16320)
* Fix #16125: `az webapp ssh`: If using a windows client, open browser to scm link (#16432)
* Fix #13291: `az webapp deployment slot swap`: The command should support preserve vnet. (#16424)
* [BREAKING CHANGE] Fix regression where you can't use a runtime version with a space in the name (#16528)

**ARM**

* `az deployment` : Add support for `--query-string` (#16447)
* `az ts`: Error handling improvement for `--template-file` without `--version` prohibited (#16446)

**Backup**

* `az backup protection backup-now`: Set default retention period to 30 days (#16500)

**Compute**

* Fix issue of none storage_profile (#16260)
* Better error handling of external tokens (#16406)
* Fix a vmss reimage issue (#16483)
* `az vm/vmss extension set`: New parameter `--enable-auto-upgrade` (#16243)

**Container**

* `az container exec`: Remove eol check to avoid closing terminal before it even started on linux (#16000)

**DMS**

* `az dms project task create`: Added task type parameter to help distinguish if a scenario is an online migration or an offline migration. (#15746)
* `az dms project task cutover`: Add new command which allows tasks with an online migration task type to cutover and end the migration. (#15746)
* `az dms project create/az dms project task create`: Enable MySQL and PostgreSQL projects/tasks to be created. (#15746)

**IoT**

* Add --tags to IoT Hub create and update (#16336)

**Monitor**

* [BREAKING CHANGE] `az monitor log-analytics workspace data-export`: Remove deprecated `--export-all-tables` parameter and require `--tables` parameter (#16402)

**RDBMS**

* Remove the preview tag for server key and ad admin commands for Postgres and MySql (#16412)

**Role**

* Fix #11594: `az role assignment create`: Only show supported values for `--assignee-principal-type` (#16056)

**Storage**

* Fix #16072: Upload file with big size (#16372)
* Fix #12291: `az storage blob generate-sas` does not properly encode `--full-uri` (#15748)
* GA PITR and blob service properties in SRP (#16540)

2.17.1
++++++

**RDBMS**

* Hotfix: `az mysql create`: Revert incorrect parameter name 'serv_name' to 'service_name'

2.17.0
++++++

**ACR**

* Support zone redundancy (#15975)
* `az acr connected-registry`: add support for private preview of connected registry feature. (#16238)
* `az acr scope-map update`: Deprecated the --add and --remove argument names, replaced with --add-repo and --remove-repo. (#16238)
* `az acr scope-map create/update`: Introduced gateway permissions to support private preview of connected registry feature. (#16238)
* `az acr token create`: Introduced synchronization tokens to support private preview of connected registry feature. (#16238)

**AKS**

* Fix: add arguments removed by a previous PR (#16080)
* `az aks get-credentials`: Clarify documentation for get-credentials (#16011)

**App Service**

* Allow customer to create Python 3.9 function app (#16296)
* Fix #14583: az webapp up should generate default name if name isn't provided (#16267)
* Fix: Better error handling when trying to create duplicate ASP in diff location (#16143)

**ARM**

* `az ts`:  Add support for --tags (#16149)
* `az ts`: Support deleting a single version (#16295)
* `az provider register`: Add --accept-terms for registering RPaaS (#16194)
* Fix parsing JSON files with multi-line strings (#15502)

**ARO**

* `az aro delete`: Add RBAC validation on cluster deletion (#16101)
* `az aro update`: Add RBAC validation on cluster update (#16213)
* Ensure worker_profile is not None before getting the subnets from (#16309)

**Backup**

* `az backup job list`: Solve -o table bug and added backup_management_type as command input (#16304)

**Batch**

* Upgrade data plane to [azure batch 10.0.0](https://pypi.org/project/azure-batch/10.0.0/) (#16156)
* [BREAKING CHANGE] az batch job task-counts: Change the output from a JSON object returning task counts to a complex JSON object that includes task counts (`taskCounts`) as well as task slot counts (`taskSlotCounts`). (#16156)

**Compute**

* New license type RHEL_ELS_6 (#16012)
* Adopt track2 SDK, azure-mgmt-compute==18.0.0 (#15750)
* [BREAKING CHANGE] Property names change due to track2 SDK. For example, `virtual_machine_extension_type` becomes `type_properties_type` in VM resource.

**Container**

* Fix misspelling in `az container create` CLI example text. (#16252)

**DataBoxEdge**

* New command module: support for data-box-edge devices and management (#16193)

**IoT**

* Update device key generation (#16129)
* Update identity-enabled hub tests to fix endpoint RBAC issues (#16128)

**Key Vault**

* `az keyvault key import`: Support `--kty` for importing BYOK keys (#16223)

**Monitor**

* `az monitor metrics alert create`: Improve error message to give more actionable insight (#16255)

**Network**

* `az network private-endpoint create`: Add more declaration of '--subnet' and '--private-connection-resource-id' (#16174)
* Change validator of application-gateway ssl-cert create (#16256)
* Migrate network to track2 SDK (#16245)
* Fix bug for "az network traffic-manager profile create" when using "--routing-method MultiValue" (#16300)

**Profile**

* Fix "missing secret or certificate in order to authenticate through a service principal" (#16219)

**Role**

* `az ad sp create-for-rbac`: Deprecate creating Contributor role assignment by default (#16081)

**Security**

* Add secure score commands (#16198)
* Fix update alert command and support new value (#16291)

**SQL**

* `az sql dw update`: do not accept backup-storage-redundancy argument (#16326)
* `az sql db update`: update backup storage redundancy as requested from command (#16326)

**Storage**

* Fix issue #15965: Clarify how to remove multiple legal hold tags with `az storage container legal-hold [clear|set]` (#16167)
* `az storage account encryption-scope`: GA support (#16270)
* Fix issue #9959: Trying to download a snapshot version of a file share fails with ResourceNotFound (#16275)

**Synapse**

* Add new cmdlets az synapse sql ad-admin show, create, update, delete (#16241)
* Add new cmdlet az synapse workspace firewall-rule update (#16241)
* Add new cmdlets az synapse sql audit-policy show, update (#16241)
* Add integration runtime related cmdlets (#15498)

2.16.0
++++++

**ACR**

* Update description for KEK param (#15866)

**AKS**

* `az aks nodepool add/update/upgrade`: Take max surge parameter (#15740)
* Add support for AGIC addon (#15993)
* Change MSI cluster to default (#16057)

**APIM**

* `az apim restore`: New command to restore a backup of an API Management service (#15933)

**App Service**

* Fix #14857: Let users update webapp config even with access restriction (#15945)
* `az functionapp create`: Accept `--runtime python` and  `--runtime-version 3.9` as Azure Functions v3 parameter (#16020)
* Fix #16041: az webapp config ssl create results in unknown error (#16124)

**ARM**

* `az deployment-scripts`: Remove preview flag (#16019)

**Backup**

* Fix #14976: CLI error improvements for ValueError and AttributeError cases (#15861)
* `az backup protection undelete`: Add support for AzureWorkload protection undelete using CLI (#15979)
* Fix Bad Request Error for Correct Workload Type Input (#15999)

**CDN**

* Add preview multi-origin support. (#15348)
* Add BYOC auto-rotation. (#15348)

**Key Vault**

* `az keyvault key/secret list`: Add a parameter `--include-managed` to list managed resources (#15926)

**Monitor**

* `az monitor metrics alert create`: Support dynamic thresholds for condition parameter (#15820)
* `az monitor metrics alert update`: Support dynamic thresholds for condition parameter (#15820)
* `az monitor metrics alert dimension create`: Build a metric alert rule dimension (#15820)
* `az monitor metrics alert condition create`: Build a metric alert rule condition (#15820)

**MySQL**

* Add MySQL version upgrade CLI (#15977)

**NetAppFiles**

* `az netappfiles account ad add`: Two optional parameters added, aes_encryption and ldap_signing (#15934)
* `az netappfiles account backup-policy update`: Three optional parameters added named tags, type and id (#15934)
* `az netappfiles snapshot policy create`: An optional parameter added named provisioning_state (#15934)

**Network**

* `az network network watcher configure`: Fix NetworkWatcherCountLimitReached error caused by case sensitivity of location value (#15801)
* `az network application-gateway http-listener`: Fix bug that cannot create and update with WAF policy name (#15929)
* `az network route-table`: Deprecate route table V1 (#16039)
* `az network cross-region-lb`: Support cross-region load balancer (#16131)
* `az network express-route port generate-loa`: New command to generate and download the PDF letter of authorization for a ExpressRoutePort (#16135)

**Packaging**

* Add Ubuntu Groovy package (#16132)

**RDBMS**

* Add single server show-connection-string and tests for local-context commands, server creation (#15844)

**Role**

* Add long-summary/warning for commands generating credentials (#15825)

**Search**

* Add SKU option (#15895)

**Service Fabric**

* Update SF app docs. only support for arm deployed resources (#16003)

**Synapse**

* Support synapse sql dw cmdlets and update az synapse workspace create cmdlet (#16095)

2.15.1
++++++

**Profile**

* Hotfix: Fix #15961: az login: UnboundLocalError: local variable 'token_entry' referenced before assignment

2.15.0
++++++

**ACS**

* Add v3 deprecation warnings (#15802)

**AKS**

* Add ephemeral os functionality (#15673)
* Engineering improvement: Replace addon strings with constants (#15786)
* `az aks install-cli`: Support customize download url (#15794)
* `az aks browse`: Point to Azure Portal Kubernetes resources view if k8s >=1.19 or kube-dashboard not enabled (#15803)
* Support BYO control plane identity (#15862)
* `az aks use-dev-spaces`: Indicate that dev-spaces commands are deprecated (#15785)

**AMS**

* Change "region" to "location" in output string: az ams account sp create (#15664)

**App Config**

* Fix key vault client initialization (#15826)

**App Service**

* Fix #13646: Unable to create App Service Plan in a different resource group to App Service Environment (#15497)
* Fix #11698 #15198 #14862 #15409: az webapp/functionapp config access-restriction add (#15784)
* `az functionapp create`: Add Node 14 preview support. (#15840)
* `az functionapp create`: Remove preview flag from custom handlers. (#15840)
* [BREAKING CHANGE] az functionapp update: Migrate a functionapp from Premium to Consumption plans now requires the '--force' flag. (#15695)
* `az functionapp update`: Add error message if functionapp migration involves any plans on Linux. (#15695)
* `az functionapp update`: Add more descriptive error message if functionapp migration fails. (#15695)

**ARM**

* Fix an issue where What-If shows two resource group scopes with different casing (#15631)
* `az deployment`: Print out error details for deployment (#15658)

**Backup**

* Fix #14976: KeyError fixed and help text improved (#15718)

**Batch**

* Fix #15464: Update check for pfx file without password in batch create_certificate (#15509)

**Billing**

* [BREAKING CHANGE] az billing invoice: Remove properties BillingPeriodsNames and DownloadUrlExpiry from the response. (#15568)
* `az billing invoice`: Support many other scopes like BillingAccount, BillingProfile and existing subscription. (#15568)
* `az billing account`: New commands to support display and update existing billing accounts. (#15568)
* `az billing balance`: New commands to support display balance of a billing profile. (#15568)
* `az billing customer`: New commands to support display customer of billing account. (#15568)
* `az billing policy`: New commands to support display and update policy of a customer or a billing profile. (#15568)
* `az billing product`: New commands to manage products of a billing account. (#15568)
* `az billing profile`: New commands to manage a billing profile. (#15568)
* `az billing property`: New commands to display and update a billing account's properties. (#15568)
* `az billing subscription`: New commands to manage the subscriptions for a billing account. (#15568)
* `az billing transaction`: New commands to list transaction of an invoice. (#15568)
* `az billing agreement`: New commands to manage billing agreement. (#15697)
* `az billing permission`: New commands to manage billing permission. (#15697)
* `az billing role-assignment`: New commands to manage role assignment. (#15697)
* `az billing role-definition`: New commands to display role definition. (#15697)
* `az billing instruction`: New commands to manage instructions of billing. (#15697)

**Compute**

* Fix update permission check issue (#15606)
* Enhancement of vm list-skus table format (#15573)
* vm host group create: Make --platform-fault-domain-count required and update help (#15751)
* Support update vm/image version when they use cross tenant images (#15883)

**DPS**

* Allow tags in IoT DPS create command (#15648)

**HDInsight**

* az hdinsight create: Add two parameters `--resource-provider-connection` and `--enable-private-link` to support relay outbound and private link feature. (#15837)

**Key Vault**

* Refine error messages for HSM `list-deleted` and `purge` (#15657)
* Support selective key restore for managed HSMs (#15867)

**NetAppFiles**

* [BREAKING CHANGE] az netappfiles pool update: Remove service-level from parameters. (#15602)
* `az netappfiles pool update`: Add optional parameter qos-type. (#15602)
* `az netappfiles pool create`: Add optional parameter qos-type. (#15602)
* `az netappfiles volume replication suspend`: Add force-break-replication as optional parameter. (#15602)
* Add az netappfiles volume replication re-initialize: New command is added to re-initialise replication. (#15602)
* Add az netappfiles volume pool-change: New command to change the pool of a volume. (#15602)
* Add az netappfiles snapshot policy: New command group with list, delete, update, show, create and volumes commands. (#15602)
* Add az netappfiles account backup: New command group with show, list and delete commands (#15602)
* Add az netappfiles volume backups: New command group with show, list, delete, update and create commands. (#15602)
* Add az netappfiles account backup-policy: New command group with show, list, delete, update and delete commands. (#15602)
* Add az netappfiles vault list: New command is added. (#15602)
* `az netappfiles account ad add`: Add optional parameters kdc-ip, ad-name, server-root-ca-certificate and backup-operators (#15602)
* `az netappfiles volumes create`: Add optional parameters snapshot-policy-id, backup-policy-id, backup-enabled, backup-id, policy-enforced, vault-id, kerberos-enabled, throughput-mibps, snapshot-directory-visible, security-style, kerberos5-read-only, kerberos5-read-write, kerberos5i-read-only, kerberos5i-read-write, kerberos5p-read-only, kerberos5p-read-write and has-root-access. (#15602)
* `az netappfiles volume update`: Add optional parameters vault-id, backup-enabled, backup-policy-id, policy-enforced and throughput-mibps (#15602)

**Network**

* Fix bug that can't create a Standard_v2 application-gateway without a private static IP address (#15757)
* `az network dns zone import`: Raise FileOperationError instead of FileNotFoundError if zone file doesn't exist (#15870)
* Fix NoneType error crash while deleting nonexisting resources of ApplicationGateway, LoadBalancer, Nic (#15886)

**Private DNS**

* `az network private-dns zone import`: Raise FileOperationError instead of FileNotFoundError if zone file doesn't exist (#15874)

**Profile**

* `az login`: Add back the warning that a browser is opened (#14505)

**Role**

* `az role assignment create`: Make `--description`, `--condition`, `--condition-version` preview (#15690)

**Security**

* `az security pricing`: Update help to reflect current API version being called (#15807)

**Storage**

* Fix #15600: az storage fs exists: in case fs does not exist ResourceNotFoundError is returned (#15643)
* Fix #15706: The examples for storage container create are incorrect (#15731)
* `az storage blob delete-batch`: Correct typo in documentation. (#15843)

2.14.2
++++++

**App Service**

* Fix #15604, #15605: Add Dotnet5 support

2.14.1
++++++

**ARM**

* Hotfix: Add TS multiline string support for template inputs

2.14.0
++++++

**AKS**

* Add PPG support (#15445)
* Update max standard load balancer timeout to 100 minutes (#15562)

**APIM**

* Fix issue with creating consumption tier instance (#15337)

**App Config**

* Fix querying key-values by comma separated labels (#15449)

**App Service**

* Bugfix: az webapp up fails when user doesn't have write permissions to project's parent directory (#15373)
* Fix #13777: Fix to remove escape chars from XML (#15364)
* Fix #15441: az webapp create-remote-connection fails with AttributeError: 'Thread' object has no attribute 'isAlive' (#15446)
* [BREAKING CHANGE] az webapp up: add optional params (os & runtime) and updated runtimes (#15522)

**ARM**

* Make template deployment What-If commands GA (#15416)
* [BREAKING CHANGE] Add user confirmation for az ts create (#15480)
* Fix the returned data when tagging multiple resources (#15146)

**Backup**

* `az backup policy create`: Add support for IaaSVM backup policy creation from CLI (#15542)
* Increasing VM protection limit from 100 to 1000 (#15563)

**Compute**

* sig image-definition create: add --features (#15549)
* New API version of gallery_images 2020-09-30 (#15549)
* `az vm update / az sig image-version update`: Support update vm/image-version even it uses a cross tenant image (#15575)
* Remove validation of vm host SKUs (#15611)

**Cosmos DB**

* `az cosmosdb create/update`: Improve error message from incorrect --locations input (#15276)
* `az cosmosdb sql container create/update`: Add --analytical-storage-ttl parameter (#15276)

**HDInsight**

* [BREAKING CHANGE] az hdinsight create: remove two parameters: --public-network-access-type and  --outbound-public-network-access-type (#15582)

**IoT Central**

* Remove preview warning since it is already GAed (#15527)

**Key Vault**

* Invalidate `--enable-soft-delete false` while creating or updating vaults (#15504)
* Make `--bypass` and `--default-action` work together with network acl parameters while creating vaults (#15571)

**Misc.**

* Add bash-completion to Dockerfile (#15228)

**RDBMS**

* Add List-SKUS Command, Table Transformers, Local Context for Postgres, MySQL, Mariadb Single Server (#15450)
* [BREAKING CHANGE] Parameter name updates. Improvements to Management Plane for MySQL and PostgreSQL (#15363)
* `az postgres|mariadb|mysql server create` : Update create experience for Postgres, MySQL and MariaDB - new fields in the output , Introduce new values for `--public` parameter in create command (all,<IP>,<IPRange>,0.0.0.0) (#15538)

**SignalR**

* `az signalr create`: Add new option `--enable-messaging-logs` for controlling service generate messaging logs or not (#15327)
* `az signalr update`: Add new option `--enable-messaging-logs` for controlling service generate messaging logs or not (#15327)

**SQL**

* [BREAKING CHANGE] Fix response for backup storage redundancy param name and value for MI (#15367)
* `az sql db audit-policy show`: extend to show database's audit policy including LA and EH data (#15444)
* `az sql db audit-policy update`: extend to allow LA and EH update along with database's audit policy (#15444)
* `az sql db audit-policy wait`: place the CLI in a waiting state until a condition of the database's audit policy is met. (#15444)
* `az sql server audit-policy show`: extend to show servers' audit policy including LA and EH data (#15444)
* `az sql server audit-policy update`: extend to allow LA and EH update along with server's audit policy (#15444)
* `az sql server audit-policy wait`: place the CLI in a waiting state until a condition of the server's audit policy is met. (#15444)
* Add AAD-only Support for SQL Managed Instances and Servers (#15292)
* `az sql db replica create`: Add --partner-database argument (#15577)

**Storage**

* Fix #15111: `az storage logging update` fails without optional argument (#15474)
* Fix bug when using set-tier command with service principal login (#15471)
* Upgrade version for file datalake to 2020-02-10 (#15572)
* `az storage queue list`: Track2 supported (#15494)
* `az storage fs access`: Support managing ACLs recursively (#15221)

**Synapse**

* Add pipeline, linked service, trigger, notebook, data flow and dataset related cmdlets (#15296)

2.13.0
++++++

**ACR**

* `az acr helm`: Update deprecation url (#15293)
* Add logtemplate and systemtask changes for ACR Tasks (#15254)

**AKS**

* Support virtual-node with aks create: `az aks create --enable-addons virtual-node` (#15129)
* Add node image only option for CLI (#15250)
* Expect kube-dashboard addon be disabled by default (#15267)
* `az aks create/update`: Add LicenseType support for Windows (#15257)
* Support add Spot node pool (#15311)
* Honor addon names defined in Azure CLI (#15376)

**AMS**

* Fix #14687: Mixed resource group and account name in command "az ams streaming-endpoint show" #14687 (#15251)

**App Config**

* Support AAD auth for data operations (#15160)

**App Service**

* `az functionapp deployment source config-zip`: Fixed an issue where config-zip could throw an exception on success on linux consumption (#15174)
* Bugfix: Better error messages for webapp commands (#15203)
* `az appservice domain create, show-terms`: Add ability to create app service domain (#15173)
* `az functionapp create`: Removed the preview flag from Java 11 when creating a new function app (#15351)
* [BREAKING CHANGE] az webapp create, az webapp up - Update available webapp runtimes (#15356)

**ARM**

* `az ts`: Add new commands for template specs
* `az deployment` : Add support for --template-spec -s (#14448)

**Compute**

* Fix host group creation FD count limitation (#15316)
* Add new command to support upgrading extensions for VMSS (#15238)
* Fix the image reference is missing issue (#14992)

**HDInsight**

* `az hdinsight create`: add deprecate information for argument --public-network-access-type and --outbound-public-network-access-type (#15181)
* `az hdinsight create`: add deprecate information for argument `--public-network-access-type` and `--outbound-public-network-access-type` (#15309)
* `az hdinsight create`:  add parameter `--idbroker` to support customer to create ESP cluster with HDInsight Id Broker (#15309)

**IoT Central**

* Remove deprecated 'az iotcentral' command module (#15114)

**Key Vault**

* Support `--hsm-name` for `az keyvault key encrypt/decrypt` (#15218)

**Lab**

* Fix #14127: `__init__()` takes 1 positional argument but 2 were given (#14827)

**Network**

* `az network application-gateway ssl-cert show`: Add example to demonstrate certificate format and fetch information (#15166)
* `az network application-gateway rule`: Support --priority option (#15222)
* `az network application-gateway create`: Fix bug that cannot create without public IP specified (#15255)
* `az network application-gateway waf-policy managed-rule rule-set add`: Expose server error to user to give more intuitive hint message. (#15261)
* `az network application-gateway waf-policy managed-rule rule-set update`: Support to change rule set type version. (#15261)

**RDBMS**

* Bugfix: az postgres flexible-server create Remove hardcoded API version from network client. (#15392)

**Role**

* Fix #15278: `az role assignment list/delete`: Forbid empty string arguments (#15282)

**SQL**

* `az sql midb log-replay`: Support for log replay service on managed database (#15168)
* Ignore character casing for backup storage redundancy param value for managed instance (#15208)
* [BREAKING CHANGE] az sql db create: Add --backup-storage-redundancy parameter; add warning for unspecified bsr/bsr == Geo. (#15341)

**SQL VM**

* `az sql vm show`: Add configuration options to --expand flag (#15156)

**Storage**

* [BREAKING CHANGE] `az storage blob copy start`: Fix format issue for `--destination-if-modified-since` and `--destination-if-unmodified-since` (#15195)
* [BREAKING CHANGE] `az storage blob incremental-copy start`: Fix format issue for `--destination-if-modified-since` and `--destination-if-unmodified-since` (#15195)
* `az storage fs`: Fix connection string issue (#15281)
* `az storage share-rm`: GA release access tier (#15344)
* `az storage container-rm`: Add a new command group to use the Microsoft.Storage resource provider for container management operations. (#15283)

2.12.1
++++++

**RDBMS**

* Hotfix: `az postgres flexible-server create` : Update VnetName to exclude servername and update default region for MySQL

2.12.0
++++++

**ACR**

* Fix #14811 Add support for dockerignore override (#14916)

**AKS**

* CLI should tolerate empty kubeconfig (#14914)
* FIX #12871: az aks enable-addons: Autogenerated help example is wrong for virtual-node option (#14989)
* Remove legacy aci connector actions (#15084)
* Support azure policy addon in azure-cli (#15092)
* Fix case sensitive issue for AKS dashboard addon (#15123)
* Update mgmt-containerservice to 9.4.0 and enable 09-01 API (#15140)

**APIM**

* Support product / productapi / namedValue entity commands && bump sdk version (#14780)

**App Config**

* Support enabling/disabling PublicNetworkAccess for existing stores (#14966)

**App Service**

* Add support for Premium V3 pricing tier (#15055)
* Fix #12653: az webapp log config --application-logging false doesn't turn it off (#14929)
* Fix #14684: access-restriction remove by ip address does not work; #13837-az webapp create - Example for different RSgroups for Plan and WebApp (#14818)
* functionapp: Add support for custom handlers. Deprecated Powershell 6.2. (#15170)
* functionapp: Fix issue where app setting was being incorrectly set for linux custom images (#15153)

**ARM**

* `az deployment group/sub/mg/tenant what-if`: Show "Ignore" resource changes last (#14932)

**Compute**

* Add new license_type in vm create/update: RHEL_BYOS, SLES_BYOS (#14934)
* Upgrade disk API version to 2020-06-30 (#15031)
* disk create: add --logical-sector-size, --tier (#15031)
* disk update: Support --disk-iops-read-only, --disk-mbps-read-only, --max-shares (#15031)
* New command disk-encryption-set list-associated-resources (#15031)
* vm boot-diagnostics enable: --storage becomes optional (#15145)
* New command: vm boot-diagnostics get-boot-log-uris (#15145)
* vm boot-diagnostics get-boot-log: support managed storage (#15145)

**Config**

* Rename local-context to config param-persist (#15068)

**Cosmos DB**

* Support for Migration APIs for Throughput resource for Autoscale feature in CosmosDB (#14887)

**Eventhub**

Added Cluster commands and trusted_service_access_enabled parameter for Networkruleset

**Extension**

* `az extension add`: Add `--upgrade` option to update the extension if already installed (#15083)
* Turn on dynamic install by default (#15081)

**IoT**

* Enabled minimum TLS version on IoT Hub Create (#14882)

**IoT Central**

* App delete operation is now long running operation (#15161)

**Iot Hub**

* Deprecated 'show-connection-string' command (#14885)

**Key Vault**

* Managed HSM public preview (#12181)
* Fix the issue that `--maxresults` does not take effect while listing resources or resource versions (#15165)

**Kusto**

* Add deprecating message (#15033)

**Monitor**

* `az monitor log-analytics workspace linked-storage`: expose detailed error message to customers (#15030)

**Network**

* `az network vnet subnet`: Support --disable-private-endpoint-network-policies and --disable-private-link-service-network-policies (#15008)
* Fix bug while updating flow-log when its subproperty network_watcher_flow_analytics_configuration is None (#15063)
* API version bump to 2020-06-01 (#15048)
* Support --tcp-port-behavior while configuring a TCP configuration of a Connection Monitor V2 (#14937)
* Support more types and coverage level while creating Endpoint of Connection Monitor V2 (#14942)
* Support --host-subnet to create VirtualHub underneath as VirtualRouter (#15151)

**RDBMS**

* Management Plane updates for PostgreSQL and MySQL (#15177)

**Role**

* `az role assignment create/update`: Support `--description`, `--condition` and `--condition-version` (#14958)
* `az ad app permission delete`: Support `--api-permissions` to delete specific `ResourceAccess` (#14815)

**Service Fabric**

* Add managed cluster and node type commands (#15101)

**SQL**

* Upgrade azure-mgmt-sql to 0.20.0 (#14728)
* Add backup storage redundancy optional parameter to MI create cmdlet (#15071)

**Storage**

* `az storage share-rm stats`: Get the usage bytes of the data stored on the share. (#14457)
* GA release storage blob PITR (#14878)
* `az storage blob query`: Support Azure Storage Query Acceleration (#14566)
* Support Soft Delete for file share (#14178)
* `az storage copy`: Add account credentials support and deprecate `--source-local-path`, `--destination-local-path`, `--destination-account-name` (#14925)
* `az storage account blob-service-properties update`: Add container delete retention policy support (#15169)

**Synapse**

* Fixed typo in example of az synapse role assignment create and delete (#14894)

2.11.1
++++++

**ACR**

* Add Isolated Tier to Agent Pool (#14952)
* Add OCI Artifact Source Context (#14576)

**AKS**

* Fix aks cluster create issue (#14920)

**Cognitive Services**

* [BREAKING CHANGE] Show additional legal term for certain APIs (#14901)

**Network**

* [BREAKING CHANGE] Allow to create both public and private IP while creating an Application Gateway (#14874)
* `az network list-service-tags`: add details on location parameter use to the help message (#14935)

**Storage**

* `az storage blob list`: Support OR properties with new api version (#14832)

2.11.0
++++++

**AKS**

* Remove preview tag from Virtual Node add-on (#14717)
* Add AKS CMK argument in cluster creation (#14688)
* Set network profile when using basic load balancer. (#14699)
* Remove max pods validation from CLI and let preflight handle it (#14750)
* Fixing add-ons available in the help message in `az aks create` (#14810)
* Bring in support for cluster autoscaler profile in core CLI (#14779)

**AppService**

* `az webapp`: Add list-instances command (#13408)
* `az webapp ssh`: Add --instance parameter to connect to a specific instance (#13408)
* `az webapp create-remote-connection`: Add --instance parameter to connect to a specific instance (#13408)
* Fix #14758: az webapp create errors when creating windows app with --runtime dotnetcore (#14764)
* Fix #14701: Implement functionapp create --assign-identity (#14702)
* Fix #11244: `az webapp auth update`: Add optional parameter to update client-secret-certificate-thumbprint (#14730)
* `az functionapp keys`: Added commands that allow users to manage their function app keys (#14465)
* `az functionapp function`: Added commands that allow users to manage their individual functions (#14465)
* `az functionapp function keys`: Added commands that allow users to manage their function keys (#14465)
* Fix #14788: az webapp create not getting correct webapp when names are substrings (#14829)
* `az functionapp create`: Removed ability to create 2.x Functions in regions that don't support it (#14831)

**ARM**

* `az resource list`: Extend the return data of `createdTime`, `changedTime` and `provisioningState` (#14704)
* `az resource`: Add parameter `--latest-include-preview` to support using the latest api-version whether this version is preview (#14589)

**ARO**

* CLI enhancements, including route table checking permissions (#14535)

**Cloud**

* `az cloud register`: Fix registering clouds with a config file (#14749)

**Compute**

* Update VM SKUs that support accelerated networking (#13045)
* `az vm create`: Automatic in-guest patching (#14710)
* `az image builder create`: Add --vm-size, --os-disk-size, --vnet, --subnet (#14685)
* New command az vm assess-patches (#14808)

**Container**

* Fix #6235: Update help text for ports parameter in container create (#14825)

**Datalake Store**

* Fix issue #14545 for data lake join operation (#14689)

**EventHub**

* `az eventhubs eventhub create/update`: Change documentation of destination_name (#12747)

**Extension**

* Add `az extension list-versions` command to list all available versions of an extension (#14803)

**HDInsight**

* Support creating cluster with autoscale configuration and Support managing autoscale configuration (#14692)
* Support creating cluster with encryption at host (#14824)

**IoTCentral**

* CLI documentation improvements (#14650)

**Monitor**

* `az monitor metrics alert create`: support RG and Sub as the scope values (#14703)

**NetAppFiles**

* [BREAKING CHANGE] az netappfiles snapshot create: Removed file-system-id from parameters (#14791)
* [BREAKING CHANGE] az netappfiles snapshot show: Snapshot no longer has parameter file-system-id (#14791)
* `az netappfiles account`: Model ActiveDirectory has a new parameter backup_operators (#14791)
* `az netappfiles volume show`: Model dataProtection has a new parameter snapshot (#14791)
* `az netappfiles volume show`: Model Volume has a new parameter snapshot_directory_visible (#14791)

**Network**

* `az network dns export`: export FQDN for MX, PTR, NS and SRV type instead of relative path (#14734)
* Support private link for managed disks (#14707)
* `az network application-gateway auth-cert show`: Add example to demonstrate certificate format (#14856)
* `az network private-endpoint-connection`: support app configuration (#14860)

**RBAC**

* `az ad group create`: support specify description when creating a group (#14668)
* `az role definition create`: print human readable message instead of exception when assignableScope is an empty array (#14663)
* [BREAKING CHANGE] `az ad sp create-for-rbac`: change default permission of created certificate (#14640)

**SQL**

* `az sql server audit-policy`: Add sql server auditing support (#14726)

**Storage**

* `az storage blob copy start-batch`: Fix #6018 for --source-sas (#14709)
* `az storage account or-policy`: Support storage account object replication policy (#14817)
* Fix issue #14083 to upgrade azure-multiapi-storage package version for package issue and new api version support (#14785)
* `az storage blob generate-sas`: add examples for --ip  and refine error message (#14854)
* `az storage blob list`: Fix next_marker issue (#14751)

**Synapse**

* Add workspace, sparkpool, sqlpool related cmdlets (#14755)
* Add spark job related commands based on track2 sdk (#14819)
* Add accesscontrol feature related commands based on track2 sdk (#14834)

**Upgrade**

* Add `az upgrade` command to upgrade azure cli and extensions (#14803)

2.10.1
++++++

**App Service**

* Fix # 9887 webapp and functionapp, support assigning/removing user managed identity (#14233)
* Fix #1382, #14055: Update error messages for az webapp create and az webapp config container set (#14633)
* `az webapp up`: Fix default ASP selection logic when --plan parameter is not provided (#14673)

**AppConfig**

* Support enabling/disabling PublicNetworkAccess during store creation (#14554)

**Compute**

* Support associating disk and snapshot with a disk-access resource (#14624)

**Lab**

* Fix for issue #7904 date validation bug in lab vm creation (#13486)

**Storage**

* `az storage blob upload-batch`: Fix issue #14660 with unpositional arguments (#14669)

2.10.0
++++++

**AKS**

* `az aks update`: Change --enable-aad argument to migrate a RBAC-enabled non-AAD cluster to a AKS-managed AAD cluster (#14420)
* `az aks install-cli`: Add --kubelogin-version and --kubelogin-install-location arguments to install kubelogin (#14441)
* Add az aks nodepool get-upgrades command (#14516)

**AMS**

* Fix #14021: az ams account sp is not idempotent (#14429)

**APIM**

* apim api import: support API import and enhance other api level cli commands (#14363)

**App Service**

* Fix #13035: Add validation for az webapp config access-restriction to avoid adding duplicates (#14486)

**AppConfig**

* Default to standard sku if not specified (#14398)
* [BREAKING CHANGE] Support settings with JSON content type (#14170)

**ARM**

* `az resource tag`: Fix the bug of managedApp tagging and some related test issues (#14381)
* `az deployment mg/tenant what-if`: Add support to management group and tenant level deployment What-If (#14568)
* `az deployment mg/tenant create`: Add --confirm-with-what-if/-c parameter. (#14568)
* `az deployment mg/tenant create`: Add --what-if-result-format/-r parameter. (#14568)
* `az deployment mg/tenant create`: Add --what-if-exclude-change-types/-x parameter. (#14568)
* `az tag`: az tag support for resource id parameter (#14558)

**Backup**

* Trigger AFS container/item discovery only when needed (#14479)

**CDN**

* Add private link fields to origin (#14520)

**Compute**

* `az vm/vmss create`: Select a valid username for user if the default username is invalid (#14346)
* `az vm update`: support cross tenant image (#14532)
* `az disk-access`: Add new command group to operate disk access resource (#14460)
* Support dedicated host group automatic placement (#14439)
* Support ppg and spg in VMSS orchestration mode (#14443)

**Config**

* `az config`: Add new `config` command module (#14436)

**Extension**

* Support automatically installing an extension if the extension of a command is not installed (#14478)

**HDInsight**

* Add 3 parameters to the command `az hdinsight create` to support private link and encryption in transit feature: (#14504)

**Iot Hub**

* Fix #7792: IoT Hub Create is not idempotent (#14449)

**IoT Central**

* Add parameter option list for iot central (#14471)

**KeyVault**

* `az keyvault key encrypt/decrypt`: add parameter `--data-type` for explicitly specifying the type of original data (#14386)

**Monitor**

* `az monitor log-analytics workspace data-export`: support event hub namespace as the destination. (#14434)
* `az monitor autoscale`: support namespace and dimensions for --condition (#14255)

**NetAppFiles**

* `az volume revert`:  Add Volume Revert to revert a volume to one of its snapshots. (#14424)
* [BREAKING CHANGE] Remove `az netappfiles mount-target`. (#14424)
* `az volume show`: Add site to Active Directory Properties (#14424)

**Network**

* `az application-gateway private-link add`: support to specify an existing subnet by ID (#14463)
* `az network application-gateway waf-policy create`: support version and type (#14531)

**Storage**

* Fix #10302: Support guess content-type when synchronizing files (#14353)
* `az storage blob lease`: Apply new api version for blob lease operations (#14231)
* `az storage fs access`: Support AAD credential in managing access control for ADLS Gen2 account (#14506)
* `az storage share-rm create/update`: add --access-tier to support access tier (#14148)

2.9.1
++++++

**AKS**

* Remove explicit setting of VMSS in Windows example command since it is now default (#14324)

**IoT**

* [BREAKING CHANGE] `az iot pnp`: Remove IoT PNP preview commands from core CLI (#14117)

**REST**

* Fix #14152: `az rest`: Accept ARM URLs without subscription ID (#14370)

**Storage**

* Fix #14138: Make some permissions optional (#14385)

2.9.0
++++++

**ACR**

* Handle log artifact link from Registry to stream logs (#14038)
* Deprecate helm2 commands (#14143)

**AKS**

* `az aks create`: add --enable-aad argument (#14068)
* `az aks update`: add --enable-aad argument (#14217)

**APIM**

* Added general az apim api commands (#13953)

**AppConfig**

* Add example for using --fields in appconfig revision (#14081)

**AppService**

* `az functionapp create`: Added support for Java 11 and Powershell 7. Added Stacks API Support. (#14063)
* Fix #14208 multi-container app creation fails (#14262)
* Fix az webapp create - use hardcoded runtime stacks (#14284)

**ARM**

* `az resource tag`: Fix the problem of tagging resources with resource type `Microsoft.ContainerInstance/containerGroups` (#14046)

**Compute**

* Bump version disks 2020-05-01, compute 2020-06-01 (#14212)
* Double encryption of disk encryption set (#14212)
* `az vmss update`: support specify cross tenant image. (#14206)
* `az sig image-version create`: support specify cross tenant image. (#14206)
* vm/vmss create: Encryption of cache & data-in-transit for OS/Data disks and temp disks for VM & VMSS (#13919)
* Add simulate-eviction operation for VM and VMSS (#14133)

**CosmosDB**

* Recent features: Autoscale, IpRules, EnableFreeTier and EnableAnalyticalStorage (#13985)

**EventGrid**

* Add CLI support for 2020-04-01-preview and mark preview features with is_Preview=True (#14027)

**Find**

* Fix #14094 az find Fix Queries failing when not logged in and when telemetry is disabled (#14243)

**HDInsight**

* Add two commands to support hdinsight node reboot feature (#14005)

**Monitor**

* Remove preview flag for commands under Log Analytics workspace (#14064)
* `az monitor diagnostic-settings subscription`: Support diagnostic settings for subscription (#14157)
* `az monitor metrics`: support ',' and '|' in metric name (#14254)
* `az monitor log-analytics workspace data-export`: support log analytics data export (#14155)

**Network**

* `az network application-gateway frontend-ip update`: Deprecating the --public-ip-address parameter (#13891)
* Bump azure-mgmt-network to 11.0.0 (#13957)
* `az network express-route gateway connection`: support routing configuration (#14256)
* `az network virtual-appliance`: Support Azure network virtual appliance. (#14224)
* Application Gateway support private link feature (#14185)

**PolicyInsights**

* `az policy state`: add trigger-scan command to trigger policy compliance evaluations (#12910)
* `az policy state list`: expose versions of policy entities in each compliance record (#12910)

**Profile**

* `az account get-access-token`: Show expiresOn for Managed Identity (#14128)

**RDBMS**

* Support Minimum TLS version (#14166)
* Add Infrastructure Encryption for Azure Postgres and MySQL (#14097)

**Security**

* Add allowed_connections commands (#14190)
* Add Adaptive network hardeningss commands (#14260)
* Add adaptive_application_controls commands (#14278)
* Addition of az security iot-solution/ iot-alerts/iot-recommendations/iot-analytics REST to Azure CLI (#14124)
* Add regulatory compliance CLI (#14103)

**SignalR**

* Add features including managing private endpoint connections, network rules and upstream (#14008)

**SQL**

* `az sql mi create`, `az sql mi update`: Add `--tags` parameter to support resource tagging (#13479)
* `az sql mi failover`: Support failover from primary or secondary point (#14242)

**Storage**

* `az storage account create/update`: Add --allow-blob-public-access to allow or disallow public access for blob and containers (#13986)
* `az storage account create/update`: Add `--min-tls-version` to support setting the minimum TLS version to be permitted on requests to storage. (#14131)
* Remove check in token credential (#14134)
* Fix the storage account name in examples (#14062)

**Webapp**

* Bugfix: az webapp log deployment show - return deployment logs instead of log metadata (#14146)
* Bugfix: az webapp vnet-integration add - fix error handling if bad vnet name, support vnet resource ID (#14101)

2.8.0
++++++

**ACR**

* Add support for region endpoint disable / routing disable (#13617)
* [BREAKING CHANGE] `az acr login --expose-token` does not accept username and password (#13874)

**ACS**

* Remove private cluster and 2019-10-27-preview API (#13618)

**AKS**

* Support --yes for az aks upgrade (#13741)
* Revert "change default vm sku to Standard_D2s_v3 (#13541)" (#13757)
* Add "az aks update --uptime-sla" (#13912)
* Fix typo in az aks update command (#14003)
* Change to support 0 node agent pool and block manual scale for CAS enabled pool (#13996)
* Fix typo on VirtualMachineScaleSets and update references to Kubernetes versions (#14022)

**AMS**

* CHANGE help text for "--expiry" parameter. (#13940)

**AppService**

* `az webapp log deployment show`: Show the latest deployment log, or the deployment logs of a specific deployment if deployment-id is specified (#13889)
* `az webapp log deployment list`: List of deployment logs available (#13889)
* Fix: Surface error when invalid webapp name provided (#13939)
* Fix #13261 az webapp list-runtimes use static list until new Available Stacks API is available (#13688)
* `az appservice ase create`: Fix create issue #13361 (#13744)
* `az appservice ase list-addresses`: Fix change of SDK #13140. (#13744)
* Fix webapp/slot creation for Windows Containers (#13813)
* `az webapp auth update`: Add optional parameter to update runtime-version (#13366)
* Support list, delete, approve and reject private endpoint connection for webapp in CLI (#13710)
* Fix #13888 : Add support for Static WebApps: get, list, create commands (#13639)
* Improved error messages for SSH Tunnel Connection (#13997)

**ARM**

* `az tag`: Add examples for -h (#10880)
* `az deployment group/sub what-if`: Add --exclude-change-types/-x parameter. (#13748)
* `az deployment group/sub/mg/tenant create`: Add --what-if-exclude-change-types/-x parameter. (#13748)
* `az deployment group/sub/mg/tenant validate`: Show error messages in a better format. (#13748)
* `az group export`: Add new parameters `--skip-resource-name-params` and `--skip-all-params` to support skip parameterization (#13558)
* Add az feature unregister api (#13487)

**ARO**

* Add Public, Private to params for help with ingress/apiserver visibility (#13550)

**Batch**

* `az batch account create`: Add new parameter `--public-network-access` (#13796)
* `az batch account create`: Add new parameter `--identity-type` (#13796)
* `az batch account set`: Add new parameter `--identity-type` (#13796)
* [BREAKING CHANGE] az batch pool create: When creating a pool using a custom image, the --image property of can now only refer to a Shared Image Gallery image. (#13796)
* [BREAKING CHANGE] az batch pool create: When creating a pool with --json-file option and specifying a networkConfiguration, the publicIPs property has moved in to a new property publicIPAddressConfiguration. This new property also supports a new ipAddressProvisioningType property which specifies how the pool should allocate IP's and a publicIPs property which allows for configuration of a list of PublicIP resources to use in the case ipAddressProvisioningType is set to UserManaged (#13796)
* `az network private-link-resource`: Add support for the Microsoft.Batch batchAccount resource (#13796)
* `az network private-endpoint-connection`: Add support for the Microsoft.Batch batchAccount resource (#13796)

**CDN**

* `az cdn custom-domain enable-https`: Add BYOC support. (#12648)
* `az cdn custom-domain enable-https`: Fix enabling custom HTTPS with CDN managed certificates for Standard_Verizon and Standard_Microsoft SKUs. (#12648)

**Cognitive Services**

* [BREAKING CHANGE] `az cognitiveservices account` now have a unified structure for all commands. (#13798)
* `az cognitiveservices account identity`: Add identity management for Cognitive Services. (#13865)

**Compute**

* `az image builder`: Upgrade API version to 2020-02-14 (#13130)
* `az image builder create`: Add `--identity` to support identity configuration (#13130)
* `az image builder customizer add`: Support Windows update customizer (#13130)
* New command `az image builder cancel` (#13130)
* Show a warning when a user deploys a VMSS pinned to a specific image version rather than latest (#14006)

**Cosmos DB**

* `az cosmosdb`: Add exists command to database and container groups (#12774)
* Allow creating fixed collections (#13950)

**EventHub**

* `az eventhubs namespace create` : Add managed identity parameters (#13992)

**Extension**

* Add --version to support to install from a specific version (#13789)
* Enable CLI extensions to include packages in the 'azure' namespace (#13163)

**Iot Hub**

* [BREAKING CHANGE] az iot hub job: Remove deprecated job commands (#13955)

**KeyVault**

* `az keyvault key import`: Supports importing from strings via two new parameters. (#13771)
* Support string/bytes encryption and decryption with stored keys (#13916)

**Monitor**

* Support no wait for cluster creation (#13787)
* `az monitor log-analytics workspace saved-search`: Support new commands for saved search (#13816)

**Network**

* `az network application-gateway address-pool update`: Refine help message and add examples. (#13780)
* `az network vnet create`: Support --nsg argument (#13842)
* `az network lb address-pool`: Support create lb backend pool with backend address. (#13700)
* `az network application-gateway address-pool`: Fix for --add argument (#14010)

**RBAC**

* `az ad sp create-for-rabc`: Support name with space, slash and back slash (#13875)
* `az ad sp create-for-rbac`: Refine error message when user specify an invalid scope (#13117)

**Security**

* Add security assessment commands (#13978)

**SQL**

* `az sql db ltr-policy/ltr-backup`: update/show long term retention policy, show/delete long term retention backups, restore long term retention backup (#12897)

**Storage**

* Fix authentication issue to support get token for --subscription (#13845)
* `az storage remove`: Fix issue #13459 to raise exception for operation failure (#13961)
* Fix issues #13012, #13632 and #13657 to remove unused arguments for generate-sas related commands (#13936)
* `az storage logging update`: Add check for logging version (#13962)
* `az storage blob show`: Add more properties for blob with track 2 SDK (#13920)
* Fix #13708: Refine warning message for credential (#13963)
* `az storage share-rm create/update`: Add NFS protocol and root squash support (#12359)
* `az storage account create`: Add support for double encryption (#13765)
* [BREAKING CHANGE] `az storage blob/container/file/share/table/queue generate-sas`: make --expiry and --permissions required (#13964)
* `az storage blob set-tier`: Migrate to Track 2 to support setting rehydrate priority (#14014)

2.7.0
++++++

**ACR**

* Fix a typo in an error message of token creation (#13620)

**AKS**

* Change default vm sku to Standard_D2s_v3 (#13541)
* Fix creating role assignment for MSI clsuter plus custom subnet (#13543)

**AppService**

* Fix #12739 az appservice list-locations returns some invalid locations (#13520)

**ARM**

* `az deployment`: Fix issue #13159 of incorrect message of JSON after removing comments and compressing (#13561)
* `az resource tag`: Fix issue #13255 of tagging resources with resource type `Microsoft.ContainerRegistry/registries/webhooks` (#13495)
* Improve the examples for the resource module (#13375)

**ARO**

* Change CLIError to correct flag for --worker-vm-disk-size-gb (#13439)

**EventHub**

* Fix for issue #12406 Argument --capture-interval does not update the "intervalInSeconds" (#13054)

**HDInsight**

* Change get_json_object to shell_safe_json_parse (#13684)

**Monitor**

* `az monitor metrics alert`: refine several help messages (#13469)
* `az monitor diagnostic-settings create`: support --export-to-resource-specific argument (#13697)
* Support LA workspace recover (#13719)

**Network**

* `az network dns zone`: support - character (#13377)
* `az network vpn-connection ipsec-policy`: change the --sa-lifetime and --sa-max-size to larger values in example (#13590)
* Bump network to 2020-04-01 (#13568)
* `az network private-endpoint-connection`: support event grid (#13608)
* `az network express-route list-route-tables`: fix bug that cannot list routes as table (#13714)

**Packaging**

* Add Ubuntu Focal Package (#13491)

**RBAC**

* `az ad sp credential reset`: modify credential generation to avoid troublesome special characters (#13643)

**Redis**

* Fix #13529: Change documentation of parameter enable_non_ssl_port (#13584)

**Storage**

* `az storage copy`: Add parameter `--follow-symlinks` to support symlinks (#12037)
* Enable local context for storage account (#13682)
* `az storage logging`: Fix issue #11969 to refine error message (#13605)

2.6.0
++++++

**ACR**

* Add default timeout of 5 minutes for any requests to ACR (#13349)
* Support disable public network access (#13347)
* `az acr token create`: expose --days argument (#13392)
* `az acr import`: accept --source argument values which contain login in server name through client end correction (#13392)

**ACS**

* Bug fix: remove fields cleanup for fields that no longer exist (#13315)

**AKS**

* Update uptime-sla command help context (#13300)
* Remove range check for updating min count for autoscaler (#13215)
* Fix that cli doe not fail when user only specifies Windows password (#13418)

**AMS**

* `az ams transform create`: Add ability to create a transform with a FaceDetector preset (#13260)
* `az ams content-key-policy create` : Add ability to create a FairPlay content key policy with an offline rental configuration (#13260)

**AppConfig**

* Bug fix for list key values with fields (#13326)

**AppService**

* `az functionapp create`: AzureWebJobsDashboard will only be set if AppInsights is disabled (#13238)
* Fix #10664- VNet Integration - Location Check Issue & fix #13257- az webapp up failing when RG needs to be created (#13106)
* `az webapp|functionapp config ssl import`: Lookup key vault across resources groups in subscription and improve help and examples. (#13099)
* Onboard local context for app service (#12984)

**ARM**

* `az deployment`: Fix the problem that the templateLink will not be returned when deploying or validating template-uri (#13317)
* `az deployment`: Fix the problem that deployment/validate does not support specially encoded character (#13137)
* `az deployment sub/group what-if`: Fix array alignment and error handling (#13295)
* `az deployment operation`: Modify the deprecate information (#13129)

**ARO**

* Add examples to az aro create, list, list-credentials, show, delete (#13403)
* Add generate_random_id function (#13482)

**Backup**

* Allow FriendlyName in enable protection for AzureFileShare command (#13268)
* Fix in IaasVM restore-disks Command (#13348)
* Add "MAB" BackupManagementType to item list command (#13449)
* Add support for retrying policy update for failed items. (#13432)
* Add Resume Protection functionality for Azure Virtual Machine (#13396)
* Add support to specify ResourceGroup for storing instantRP during Create or Modify Policy (#13376)

**CI**

* Support flake8 3.8.0 (#13454)

**Compute**

* New command az vm auto-shutdown (#13199)
* `az vm list-skus`: Update --zone behavior, return all type skus now (#13470)

**Core**

* Update local context on/off status to global user level (#13277)

**Extension**

* `az extension add`: Add --system to enable installing extensions in a system path (#12856)
* Support .egg-info to store wheel type extension metadata (#13286)

**IoT**

* `az iot`: Update the IoT command module first run extension awareness message to the accurate, non-deprecated modern Id `azure-iot`. (#13097)

**IoT Hub**

* Support for 2020-03-01 API and Network Isolation commands (#13467)

**NetAppFiles**

* `az volume create`: Adds snapshot-id as a parameter to create volume this will allow users to create a volume from existing snapshot. (#13481)

**Network**

* Fix ttl value changed unintended for dns add-record (#13243)
* `az network public-ip create`: Inform customers of a coming breaking change (#13395)
* Support generic commands for private link scenario (#13225)
* `az network private-endpoint-connection`: Support mysql, postgre and mariadb types (#13433)
* `az network private-endpoint-connection`: Support cosmosdb types (#13452)
* `az network private-endpoint`: deprecate --group-ids and redirect to --group-id (#13511)

**Output**

* Show update instruction in find, feedback and --help (#13345)

**Packaging**

* Build MSI/Homebrew packages with dependecies resolved from requirements.txt (#13353)

**RBAC**

* `az ad sp credential reset`: fix weak credential generation (#13357)

**Storage**

* `az storage account file-service-properties update/show`: Add File Properties Support for Storage Account (#12333)
* `az storage container create`: Fix #13373 by adding validator for public access (#13496)
* Add ADLS Gen2 track2 support (#12729)
* `az storage blob sync`: Support `--connection-string` (#11880)
* `az storage blob sync`: Fix the incorrect error message when azcopy cannot find the installation location (#9576)

2.5.1
++++++

**ACR**

* `az acr check-health`: Fix "DOCKER_PULL_ERROR" on Windows (#13158)

**Compute**

* `az vm list-ip-addresses`: Error handling (#13186)
* Fix a bug of vm create if endpoint_vm_image_alias_doc is not set in cloud profile (#13022)
* `az vmss create`: Add --os-disk-size-gb (#13180)

**Cosmos DB**

* `az cosmosdb create/update`: add --enable-public-network support (#13109)

**Extension**

* Fix loading wrong metadata for wheel type extension (#13222)

**Packaging**

* Add az script for Git Bash/Cygwin on Windows (#13197)

**SQL**

* `az sql instance-pool`: Add instance pools command group (#11721)

**Storage**

* Upgrade package azure-multiapi-storage to 0.3.0 (#13183)
* Support GZRS for storage account creation and update (#13196)
* `az storage account failover`: Add support for grs/gzrs storage account failover (#13201)
* `az storage blob upload`: Add --encryption-scope parameter to support specifying encryption scope information (#13246)

2.5.0
++++++

**ACS**

* [BREAKING CHANGE] az openshift create: remove --vnet-peer parameter. (#12240)
* `az openshift create`: add flags to support private cluster. (#12240)
* `az openshift`: upgrade to `2019-10-27-preview` API version. (#12240)
* `az openshift`: add `update` command. (#12240)

**AKS**

* `az aks create`: Add support for Windows (#13084)

**AppService**

* `az webapp deployment source config-zip`: remove sleep after request.get() (#12609)

**ARM**

* Add template deployment What-If commands (#12942)

**ARO**

* `az aro`: Fix table output (#13066)

**CI**

* Onboard pytest and deprecate nose for Automation Test (#13153)

**Compute**

* `az vmss disk detach`: fix data disk NoneType issue (#13069)
* `az vm availability-set list`: Support showing VM list (#13090)
* `az vm list-skus`: Fix display problem of table format (#13184)

**KeyVault**

* Add new parameter `--enable-rbac-authorization` during creating or updating (#12074)

**Monitor**

* Support LA cluster CMK features (#13133)
* `az monitor log-analytics workspace linked-storage`: supports BYOS features (#13187)

**Network**

* `az network security-partner`: support security partner provider (#13118)

**Privatedns**

* Add feature in private DNS zone to import export zone file (#13062)

2.4.0
++++++

**ACR**

* `az acr run --cmd`: disable working directory override (#12877)
* Support dedicated data endpoint (#12967)

**AKS**

* `az aks list -o table` should show privateFqdn as fqdn for private clusters (#12784)
* Add --uptime-sla (#12772)
* Update containerservice package (#12964)
* Add node public IP support. (#13015)
* Fix typo in the help command (#13055)

**AppConfig**

* Resolve key vault reference for kv list and export commands (#12893)
* Bug fix for list key values (#12926)

**AppService**

* `az functionapp create`: Changed the way linuxFxVersion was being set for dotnet linux function apps. This should fix a bug that was preventing dotnet linux consumption apps from being created. (#12817)
* [BREAKING CHANGE] `az webapp create`: fix to keep existing AppSettings with az webapp create. (#12865)
* [BREAKING CHANGE] `az webapp up`: fix to create RG for az webapp up command when using -g flag. (#12865)
* [BREAKING CHANGE] `az webapp config`: fix to show values for non-JSON output with az webapp config connection-string list (#12865)

**ARM**

* `az deployment create/validate`: Add parameter `--no-prompt` to support skipping the prompt of missing parameters for ARM template (#11972)
* `az deployment group/mg/sub/tenant validate`: Support comments in deployment parameter file (#12389)
* `az deployment`: Remove `is_preview` for parameter `--handle-extended-json-format` (#12943)
* `az deployment group/mg/sub/tenant cancel`: Support cancel deployment for ARM template (#12252)
* `az deployment group/mg/sub/tenant validate`: Improve the error message when deployment verification fails (#12241)
* `az deployment-scripts`: Add new commands for DeploymentScripts (#12928)
* `az resource tag`: Add parameter `--is-incremental` to support adding tags to resource incrementally (#12736)

**ARO**

* `az aro`:  Add Azure RedHat OpenShift V4 aro command module (#12793)

**Batch**

* Update Batch API (#12813)

**Compute**

* `az sig image-version create`: Add storage account type Premium_LRS (#12919)
* `az vmss update`: Fix terminate notification update issue (#12948)
* `az vm/vmss create`: Add support for specialized image version (#12997)
* SIG API Version 2019-12-01. (#12899)
* `az sig image-version create`: Add --target-region-encryption. (#12899)
* Fix tests fail when running in serial due to keyvault name is duplicated in global in-memory cache

**CosmosDB**

* Support `az cosmosdb private-link-resource/private-endpoint-connection` (#12960)

**IoT Central**

* Deprecate `az iotcentral` (#12681)
* Add `az iot central` command module (#12681)

**Monitor**

* Support private link scenario for monitor (#12931)
* Fix wrong mocking way in test_monitor_general_operations.py

**Network**

* Deprecate sku for public ip update command (#12898)
* `az network private-endpoint`: Support private dns zone group. (#13038)
* Enable local context feature for vnet/subnet parameter (#13059)
* Fix wrong usage example in test_nw_flow_log_delete

**Packaging**

* Drop support for Ubuntu/Disco package (#13036)

**RBAC**

* `az ad app create/update`: support --optional-claims as a parameter (#12954)

**RDBMS**

* Add Azure active directory administrator commands for PostgreSQL and MySQL (#12812)

**Service Fabric**

* Fix #12891: `az sf application update --application-parameters` removes old parameters that are not in the request (#12992)
* Fix #12470 az sf create cluster, fix bugs in update durability and reliability and find vmss correctly through the code given a node type name (#12731)

**SQL**

* Add `az sql mi op list`, `az sql mi op get`, `az sql mi op cancel` (#12667)
* `az sql midb`: update/show long term retention policy,  show/delete long term retention backups, restore long term retention backup (#12712)

**Storage**

* Upgrade azure-mgmt-storage to 9.0.0 (#12799)
* `az storage logging off`: Support turning off logging for a storage account (#12918)
* `az storage account update`: Enable key auto-rotated for CMK (#12932)
* `az storage account encryption-scope create/update/list/show`: Add support to customize encryption scope. (#12425)
* `az storage container create`: Add --default-encryption-scope and --deny-encryption-scope-override to set encryption scope for container level. (#12425)

**Survey**

* Add switch to turn off survey link (#13041)

2.3.1
++++++

**ACR**

* Fix wrong version of azure-mgmt-containerregistry for Linux

**Profile**

* az login: Fix login failure with cloud profiles other than `latest`

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
* `az storage remove`: Change `--include` and `--exclude` parameters to `--include-path`, `--include-pattern`, `--exclude-path` and`--exclude-pattern` parameters
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
* database: Add deprecation information
* collection: Add deprecation information

**IoT**

* Add new routing source type: DigitalTwinChangeEvents
* Fix #2826: Missing features in "az iot hub create"
* Bug Fixed: Return more descriptive message on raised exception.

**Key Vault**

* Fix #9352: Unexpected error when certificate file does not exist
* Fix #7048: `az keyvault recover/purge` not working

**Monitor**

* Updated azure-mgmt-monitor to 0.7.0
* az monitor action-group create/update: Added support for following new receivers: Arm role, Azure app push, ITSM, automation runbook, voice, logic app and Azure function
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
* Add `az aks nodepool add`,`az aks nodepool show`, `az aks nodepool list`, `az aks nodepool scale`, `az aks nodepool upgrade`, `az aks nodepool update` and `az aks nodepool delete` commands to support multiple nodepools in aks
* Add `--zones` to `az aks create` and `az aks nodepool add` commands to support availability zones for aks
* Enable GA support of apiserver authorized IP ranges via parameter `--api-server-authorized-ip-ranges` in `az aks create` and `az aks update`

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

* Introduced initial implementation of API Management preview commands (az apim)

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
* network dns record-set ns create: Fixes #9965. Support --subscription again by moving the suppression into lower scope.
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

* Fixed issue #8775 : Cannot create hybrid connection with disabled client authorization
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

* vmss create: Fix bug where command returns an error message when run with `--no-wait`. The command successfully sends
  the request but returns failure status code and returns an error message.
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
