# Azure CLI Module Creation Report

## EXTENSION
|CLI Extension|Command Groups|
|---------|------------|
|az synapse|[groups](#CommandGroups)

## GROUPS
### <a name="CommandGroups">Command groups in `az synapse` extension </a>
|CLI Command Group|Group Swagger name|Commands|
|---------|------------|--------|
|az synapse kusto attached-database-configuration|KustoPoolAttachedDatabaseConfigurations|[commands](#CommandsInKustoPoolAttachedDatabaseConfigurations)|
|az synapse kusto data-connection|KustoPoolDataConnections|[commands](#CommandsInKustoPoolDataConnections)|
|az synapse kusto database|KustoPoolDatabases|[commands](#CommandsInKustoPoolDatabases)|
|az synapse kusto database-principal-assignment|KustoPoolDatabasePrincipalAssignments|[commands](#CommandsInKustoPoolDatabasePrincipalAssignments)|
|az synapse kusto pool|KustoPool|[commands](#CommandsInKustoPool)|
|az synapse kusto pool|KustoPools|[commands](#CommandsInKustoPools)|
|az synapse kusto pool-principal-assignment|KustoPoolPrincipalAssignments|[commands](#CommandsInKustoPoolPrincipalAssignments)|
|az synapse kusto-operation|KustoOperations|[commands](#CommandsInKustoOperations)|

## COMMANDS
### <a name="CommandsInKustoPoolAttachedDatabaseConfigurations">Commands in `az synapse kusto attached-database-configuration` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az synapse kusto attached-database-configuration list](#KustoPoolAttachedDatabaseConfigurationsListByKustoPool)|ListByKustoPool|[Parameters](#ParametersKustoPoolAttachedDatabaseConfigurationsListByKustoPool)|[Example](#ExamplesKustoPoolAttachedDatabaseConfigurationsListByKustoPool)|
|[az synapse kusto attached-database-configuration show](#KustoPoolAttachedDatabaseConfigurationsGet)|Get|[Parameters](#ParametersKustoPoolAttachedDatabaseConfigurationsGet)|[Example](#ExamplesKustoPoolAttachedDatabaseConfigurationsGet)|
|[az synapse kusto attached-database-configuration create](#KustoPoolAttachedDatabaseConfigurationsCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersKustoPoolAttachedDatabaseConfigurationsCreateOrUpdate#Create)|[Example](#ExamplesKustoPoolAttachedDatabaseConfigurationsCreateOrUpdate#Create)|
|[az synapse kusto attached-database-configuration update](#KustoPoolAttachedDatabaseConfigurationsCreateOrUpdate#Update)|CreateOrUpdate#Update|[Parameters](#ParametersKustoPoolAttachedDatabaseConfigurationsCreateOrUpdate#Update)|Not Found|
|[az synapse kusto attached-database-configuration delete](#KustoPoolAttachedDatabaseConfigurationsDelete)|Delete|[Parameters](#ParametersKustoPoolAttachedDatabaseConfigurationsDelete)|[Example](#ExamplesKustoPoolAttachedDatabaseConfigurationsDelete)|

### <a name="CommandsInKustoPoolDataConnections">Commands in `az synapse kusto data-connection` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az synapse kusto data-connection list](#KustoPoolDataConnectionsListByDatabase)|ListByDatabase|[Parameters](#ParametersKustoPoolDataConnectionsListByDatabase)|[Example](#ExamplesKustoPoolDataConnectionsListByDatabase)|
|[az synapse kusto data-connection show](#KustoPoolDataConnectionsGet)|Get|[Parameters](#ParametersKustoPoolDataConnectionsGet)|[Example](#ExamplesKustoPoolDataConnectionsGet)|
|[az synapse kusto data-connection event-grid create](#KustoPoolDataConnectionsCreateOrUpdate#Create#EventGrid)|CreateOrUpdate#Create#EventGrid|[Parameters](#ParametersKustoPoolDataConnectionsCreateOrUpdate#Create#EventGrid)|Not Found|
|[az synapse kusto data-connection event-hub create](#KustoPoolDataConnectionsCreateOrUpdate#Create#EventHub)|CreateOrUpdate#Create#EventHub|[Parameters](#ParametersKustoPoolDataConnectionsCreateOrUpdate#Create#EventHub)|[Example](#ExamplesKustoPoolDataConnectionsCreateOrUpdate#Create#EventHub)|
|[az synapse kusto data-connection iot-hub create](#KustoPoolDataConnectionsCreateOrUpdate#Create#IotHub)|CreateOrUpdate#Create#IotHub|[Parameters](#ParametersKustoPoolDataConnectionsCreateOrUpdate#Create#IotHub)|Not Found|
|[az synapse kusto data-connection event-grid update](#KustoPoolDataConnectionsUpdate#EventGrid)|Update#EventGrid|[Parameters](#ParametersKustoPoolDataConnectionsUpdate#EventGrid)|Not Found|
|[az synapse kusto data-connection event-hub update](#KustoPoolDataConnectionsUpdate#EventHub)|Update#EventHub|[Parameters](#ParametersKustoPoolDataConnectionsUpdate#EventHub)|[Example](#ExamplesKustoPoolDataConnectionsUpdate#EventHub)|
|[az synapse kusto data-connection iot-hub update](#KustoPoolDataConnectionsUpdate#IotHub)|Update#IotHub|[Parameters](#ParametersKustoPoolDataConnectionsUpdate#IotHub)|Not Found|
|[az synapse kusto data-connection delete](#KustoPoolDataConnectionsDelete)|Delete|[Parameters](#ParametersKustoPoolDataConnectionsDelete)|[Example](#ExamplesKustoPoolDataConnectionsDelete)|

### <a name="CommandsInKustoPoolDatabases">Commands in `az synapse kusto database` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az synapse kusto database list](#KustoPoolDatabasesListByKustoPool)|ListByKustoPool|[Parameters](#ParametersKustoPoolDatabasesListByKustoPool)|[Example](#ExamplesKustoPoolDatabasesListByKustoPool)|
|[az synapse kusto database show](#KustoPoolDatabasesGet)|Get|[Parameters](#ParametersKustoPoolDatabasesGet)|[Example](#ExamplesKustoPoolDatabasesGet)|
|[az synapse kusto database create](#KustoPoolDatabasesCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersKustoPoolDatabasesCreateOrUpdate#Create)|[Example](#ExamplesKustoPoolDatabasesCreateOrUpdate#Create)|
|[az synapse kusto database update](#KustoPoolDatabasesUpdate)|Update|[Parameters](#ParametersKustoPoolDatabasesUpdate)|[Example](#ExamplesKustoPoolDatabasesUpdate)|
|[az synapse kusto database delete](#KustoPoolDatabasesDelete)|Delete|[Parameters](#ParametersKustoPoolDatabasesDelete)|[Example](#ExamplesKustoPoolDatabasesDelete)|

### <a name="CommandsInKustoPoolDatabasePrincipalAssignments">Commands in `az synapse kusto database-principal-assignment` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az synapse kusto database-principal-assignment list](#KustoPoolDatabasePrincipalAssignmentsList)|List|[Parameters](#ParametersKustoPoolDatabasePrincipalAssignmentsList)|[Example](#ExamplesKustoPoolDatabasePrincipalAssignmentsList)|
|[az synapse kusto database-principal-assignment show](#KustoPoolDatabasePrincipalAssignmentsGet)|Get|[Parameters](#ParametersKustoPoolDatabasePrincipalAssignmentsGet)|[Example](#ExamplesKustoPoolDatabasePrincipalAssignmentsGet)|
|[az synapse kusto database-principal-assignment create](#KustoPoolDatabasePrincipalAssignmentsCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersKustoPoolDatabasePrincipalAssignmentsCreateOrUpdate#Create)|[Example](#ExamplesKustoPoolDatabasePrincipalAssignmentsCreateOrUpdate#Create)|
|[az synapse kusto database-principal-assignment update](#KustoPoolDatabasePrincipalAssignmentsCreateOrUpdate#Update)|CreateOrUpdate#Update|[Parameters](#ParametersKustoPoolDatabasePrincipalAssignmentsCreateOrUpdate#Update)|Not Found|
|[az synapse kusto database-principal-assignment delete](#KustoPoolDatabasePrincipalAssignmentsDelete)|Delete|[Parameters](#ParametersKustoPoolDatabasePrincipalAssignmentsDelete)|[Example](#ExamplesKustoPoolDatabasePrincipalAssignmentsDelete)|

### <a name="CommandsInKustoPool">Commands in `az synapse kusto pool` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az synapse kusto pool list-sku](#KustoPoolListSkus)|ListSkus|[Parameters](#ParametersKustoPoolListSkus)|[Example](#ExamplesKustoPoolListSkus)|

### <a name="CommandsInKustoPools">Commands in `az synapse kusto pool` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az synapse kusto pool list](#KustoPoolsListByWorkspace)|ListByWorkspace|[Parameters](#ParametersKustoPoolsListByWorkspace)|[Example](#ExamplesKustoPoolsListByWorkspace)|
|[az synapse kusto pool show](#KustoPoolsGet)|Get|[Parameters](#ParametersKustoPoolsGet)|[Example](#ExamplesKustoPoolsGet)|
|[az synapse kusto pool delete](#KustoPoolsDelete)|Delete|[Parameters](#ParametersKustoPoolsDelete)|[Example](#ExamplesKustoPoolsDelete)|
|[az synapse kusto pool list-follower-database](#KustoPoolsListFollowerDatabases)|ListFollowerDatabases|[Parameters](#ParametersKustoPoolsListFollowerDatabases)|[Example](#ExamplesKustoPoolsListFollowerDatabases)|
|[az synapse kusto pool list-language-extension](#KustoPoolsListLanguageExtensions)|ListLanguageExtensions|[Parameters](#ParametersKustoPoolsListLanguageExtensions)|[Example](#ExamplesKustoPoolsListLanguageExtensions)|
|[az synapse kusto pool list-sku](#KustoPoolsListSkusByResource)|ListSkusByResource|[Parameters](#ParametersKustoPoolsListSkusByResource)|[Example](#ExamplesKustoPoolsListSkusByResource)|
|[az synapse kusto pool start](#KustoPoolsStart)|Start|[Parameters](#ParametersKustoPoolsStart)|[Example](#ExamplesKustoPoolsStart)|
|[az synapse kusto pool stop](#KustoPoolsStop)|Stop|[Parameters](#ParametersKustoPoolsStop)|[Example](#ExamplesKustoPoolsStop)|

### <a name="CommandsInKustoPoolPrincipalAssignments">Commands in `az synapse kusto pool-principal-assignment` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az synapse kusto pool-principal-assignment list](#KustoPoolPrincipalAssignmentsList)|List|[Parameters](#ParametersKustoPoolPrincipalAssignmentsList)|[Example](#ExamplesKustoPoolPrincipalAssignmentsList)|
|[az synapse kusto pool-principal-assignment show](#KustoPoolPrincipalAssignmentsGet)|Get|[Parameters](#ParametersKustoPoolPrincipalAssignmentsGet)|[Example](#ExamplesKustoPoolPrincipalAssignmentsGet)|
|[az synapse kusto pool-principal-assignment create](#KustoPoolPrincipalAssignmentsCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersKustoPoolPrincipalAssignmentsCreateOrUpdate#Create)|[Example](#ExamplesKustoPoolPrincipalAssignmentsCreateOrUpdate#Create)|
|[az synapse kusto pool-principal-assignment update](#KustoPoolPrincipalAssignmentsCreateOrUpdate#Update)|CreateOrUpdate#Update|[Parameters](#ParametersKustoPoolPrincipalAssignmentsCreateOrUpdate#Update)|Not Found|
|[az synapse kusto pool-principal-assignment delete](#KustoPoolPrincipalAssignmentsDelete)|Delete|[Parameters](#ParametersKustoPoolPrincipalAssignmentsDelete)|[Example](#ExamplesKustoPoolPrincipalAssignmentsDelete)|

### <a name="CommandsInKustoOperations">Commands in `az synapse kusto-operation` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az synapse kusto-operation list](#KustoOperationsList)|List|[Parameters](#ParametersKustoOperationsList)|[Example](#ExamplesKustoOperationsList)|


## COMMAND DETAILS
### group `az synapse kusto attached-database-configuration`
#### <a name="KustoPoolAttachedDatabaseConfigurationsListByKustoPool">Command `az synapse kusto attached-database-configuration list`</a>

##### <a name="ExamplesKustoPoolAttachedDatabaseConfigurationsListByKustoPool">Example</a>
```
az synapse kusto attached-database-configuration list --kusto-pool-name "kustoclusterrptest4" --resource-group \
"kustorptest" --workspace-name "kustorptest"
```
##### <a name="ParametersKustoPoolAttachedDatabaseConfigurationsListByKustoPool">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

#### <a name="KustoPoolAttachedDatabaseConfigurationsGet">Command `az synapse kusto attached-database-configuration show`</a>

##### <a name="ExamplesKustoPoolAttachedDatabaseConfigurationsGet">Example</a>
```
az synapse kusto attached-database-configuration show --attached-database-configuration-name \
"attachedDatabaseConfigurations1" --kusto-pool-name "kustoclusterrptest4" --resource-group "kustorptest" \
--workspace-name "kustorptest"
```
##### <a name="ParametersKustoPoolAttachedDatabaseConfigurationsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--attached-database-configuration-name**|string|The name of the attached database configuration.|attached_database_configuration_name|attachedDatabaseConfigurationName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

#### <a name="KustoPoolAttachedDatabaseConfigurationsCreateOrUpdate#Create">Command `az synapse kusto attached-database-configuration create`</a>

##### <a name="ExamplesKustoPoolAttachedDatabaseConfigurationsCreateOrUpdate#Create">Example</a>
```
az synapse kusto attached-database-configuration create --attached-database-configuration-name \
"attachedDatabaseConfigurations1" --kusto-pool-name "kustoclusterrptest4" --location "westus" --kusto-pool-resource-id \
"/subscriptions/12345678-1234-1234-1234-123456789098/resourceGroups/kustorptest/providers/Microsoft.Synapse/Workspaces/\
kustorptest/KustoPools/kustoclusterrptest4" --database-name "kustodatabase" --default-principals-modification-kind \
"Union" --table-level-sharing-properties external-tables-to-exclude="ExternalTable2" external-tables-to-include="Extern\
alTable1" materialized-views-to-exclude="MaterializedViewTable2" materialized-views-to-include="MaterializedViewTable1"\
 tables-to-exclude="Table2" tables-to-include="Table1" --resource-group "kustorptest" --workspace-name "kustorptest"
```
##### <a name="ParametersKustoPoolAttachedDatabaseConfigurationsCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--attached-database-configuration-name**|string|The name of the attached database configuration.|attached_database_configuration_name|attachedDatabaseConfigurationName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--location**|string|Resource location.|location|location|
|**--database-name**|string|The name of the database which you would like to attach, use * if you want to follow all current and future databases.|database_name|databaseName|
|**--kusto-pool-resource-id**|string|The resource id of the kusto pool where the databases you would like to attach reside.|kusto_pool_resource_id|kustoPoolResourceId|
|**--default-principals-modification-kind**|choice|The default principals modification kind|default_principals_modification_kind|defaultPrincipalsModificationKind|
|**--table-level-sharing-properties**|object|Table level sharing specifications|table_level_sharing_properties|tableLevelSharingProperties|

#### <a name="KustoPoolAttachedDatabaseConfigurationsCreateOrUpdate#Update">Command `az synapse kusto attached-database-configuration update`</a>


##### <a name="ParametersKustoPoolAttachedDatabaseConfigurationsCreateOrUpdate#Update">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--attached-database-configuration-name**|string|The name of the attached database configuration.|attached_database_configuration_name|attachedDatabaseConfigurationName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--location**|string|Resource location.|location|location|
|**--database-name**|string|The name of the database which you would like to attach, use * if you want to follow all current and future databases.|database_name|databaseName|
|**--kusto-pool-resource-id**|string|The resource id of the kusto pool where the databases you would like to attach reside.|kusto_pool_resource_id|kustoPoolResourceId|
|**--default-principals-modification-kind**|choice|The default principals modification kind|default_principals_modification_kind|defaultPrincipalsModificationKind|
|**--table-level-sharing-properties**|object|Table level sharing specifications|table_level_sharing_properties|tableLevelSharingProperties|

#### <a name="KustoPoolAttachedDatabaseConfigurationsDelete">Command `az synapse kusto attached-database-configuration delete`</a>

##### <a name="ExamplesKustoPoolAttachedDatabaseConfigurationsDelete">Example</a>
```
az synapse kusto attached-database-configuration delete --attached-database-configuration-name \
"attachedDatabaseConfigurations1" --kusto-pool-name "kustoclusterrptest4" --resource-group "kustorptest" \
--workspace-name "kustorptest"
```
##### <a name="ParametersKustoPoolAttachedDatabaseConfigurationsDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--attached-database-configuration-name**|string|The name of the attached database configuration.|attached_database_configuration_name|attachedDatabaseConfigurationName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

### group `az synapse kusto data-connection`
#### <a name="KustoPoolDataConnectionsListByDatabase">Command `az synapse kusto data-connection list`</a>

##### <a name="ExamplesKustoPoolDataConnectionsListByDatabase">Example</a>
```
az synapse kusto data-connection list --database-name "KustoDatabase8" --kusto-pool-name "kustoclusterrptest4" \
--resource-group "kustorptest" --workspace-name "synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDataConnectionsListByDatabase">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|

#### <a name="KustoPoolDataConnectionsGet">Command `az synapse kusto data-connection show`</a>

##### <a name="ExamplesKustoPoolDataConnectionsGet">Example</a>
```
az synapse kusto data-connection show --data-connection-name "DataConnections8" --database-name "KustoDatabase8" \
--kusto-pool-name "kustoclusterrptest4" --resource-group "kustorptest" --workspace-name "synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDataConnectionsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--data-connection-name**|string|The name of the data connection.|data_connection_name|dataConnectionName|

#### <a name="KustoPoolDataConnectionsCreateOrUpdate#Create#EventGrid">Command `az synapse kusto data-connection event-grid create`</a>


##### <a name="ParametersKustoPoolDataConnectionsCreateOrUpdate#Create#EventGrid">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--data-connection-name**|string|The name of the data connection.|data_connection_name|dataConnectionName|
|**--location**|string|Resource location.|event_grid_location|location|
|**--storage-account-resource-id**|string|The resource ID of the storage account where the data resides.|event_grid_storage_account_resource_id|storageAccountResourceId|
|**--event-hub-resource-id**|string|The resource ID where the event grid is configured to send events.|event_grid_event_hub_resource_id|eventHubResourceId|
|**--consumer-group**|string|The event hub consumer group.|event_grid_consumer_group|consumerGroup|
|**--table-name**|string|The table where the data should be ingested. Optionally the table information can be added to each message.|event_grid_table_name|tableName|
|**--mapping-rule-name**|string|The mapping rule to be used to ingest the data. Optionally the mapping information can be added to each message.|event_grid_mapping_rule_name|mappingRuleName|
|**--data-format**|choice|The data format of the message. Optionally the data format can be added to each message.|event_grid_data_format|dataFormat|
|**--ignore-first-record**|boolean|A Boolean value that, if set to true, indicates that ingestion should ignore the first record of every file|event_grid_ignore_first_record|ignoreFirstRecord|
|**--blob-storage-event-type**|choice|The name of blob storage event type to process.|event_grid_blob_storage_event_type|blobStorageEventType|

#### <a name="KustoPoolDataConnectionsCreateOrUpdate#Create#EventHub">Command `az synapse kusto data-connection event-hub create`</a>

##### <a name="ExamplesKustoPoolDataConnectionsCreateOrUpdate#Create#EventHub">Example</a>
```
az synapse kusto data-connection event-hub create --data-connection-name "DataConnections8" --database-name \
"KustoDatabase8" --kusto-pool-name "kustoclusterrptest4" --location "westus" --consumer-group "testConsumerGroup1" \
--event-hub-resource-id "/subscriptions/12345678-1234-1234-1234-123456789098/resourceGroups/kustorptest/providers/Micro\
soft.EventHub/namespaces/eventhubTestns1/eventhubs/eventhubTest1" --resource-group "kustorptest" --workspace-name \
"synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDataConnectionsCreateOrUpdate#Create#EventHub">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--data-connection-name**|string|The name of the data connection.|data_connection_name|dataConnectionName|
|**--location**|string|Resource location.|event_hub_location|location|
|**--event-hub-resource-id**|string|The resource ID of the event hub to be used to create a data connection.|event_hub_event_hub_resource_id|eventHubResourceId|
|**--consumer-group**|string|The event hub consumer group.|event_hub_consumer_group|consumerGroup|
|**--table-name**|string|The table where the data should be ingested. Optionally the table information can be added to each message.|event_hub_table_name|tableName|
|**--mapping-rule-name**|string|The mapping rule to be used to ingest the data. Optionally the mapping information can be added to each message.|event_hub_mapping_rule_name|mappingRuleName|
|**--data-format**|choice|The data format of the message. Optionally the data format can be added to each message.|event_hub_data_format|dataFormat|
|**--event-system-properties**|array|System properties of the event hub|event_hub_event_system_properties|eventSystemProperties|
|**--compression**|choice|The event hub messages compression type|event_hub_compression|compression|
|**--managed-identity-resource-id**|string|The resource ID of a managed identity (system or user assigned) to be used to authenticate with event hub.|event_hub_managed_identity_resource_id|managedIdentityResourceId|

#### <a name="KustoPoolDataConnectionsCreateOrUpdate#Create#IotHub">Command `az synapse kusto data-connection iot-hub create`</a>


##### <a name="ParametersKustoPoolDataConnectionsCreateOrUpdate#Create#IotHub">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--data-connection-name**|string|The name of the data connection.|data_connection_name|dataConnectionName|
|**--location**|string|Resource location.|iot_hub_location|location|
|**--iot-hub-resource-id**|string|The resource ID of the Iot hub to be used to create a data connection.|iot_hub_iot_hub_resource_id|iotHubResourceId|
|**--consumer-group**|string|The iot hub consumer group.|iot_hub_consumer_group|consumerGroup|
|**--table-name**|string|The table where the data should be ingested. Optionally the table information can be added to each message.|iot_hub_table_name|tableName|
|**--mapping-rule-name**|string|The mapping rule to be used to ingest the data. Optionally the mapping information can be added to each message.|iot_hub_mapping_rule_name|mappingRuleName|
|**--data-format**|choice|The data format of the message. Optionally the data format can be added to each message.|iot_hub_data_format|dataFormat|
|**--event-system-properties**|array|System properties of the iot hub|iot_hub_event_system_properties|eventSystemProperties|
|**--shared-access-policy-name**|string|The name of the share access policy|iot_hub_shared_access_policy_name|sharedAccessPolicyName|

#### <a name="KustoPoolDataConnectionsUpdate#EventGrid">Command `az synapse kusto data-connection event-grid update`</a>


##### <a name="ParametersKustoPoolDataConnectionsUpdate#EventGrid">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--data-connection-name**|string|The name of the data connection.|data_connection_name|dataConnectionName|
|**--location**|string|Resource location.|event_grid_location|location|
|**--storage-account-resource-id**|string|The resource ID of the storage account where the data resides.|event_grid_storage_account_resource_id|storageAccountResourceId|
|**--event-hub-resource-id**|string|The resource ID where the event grid is configured to send events.|event_grid_event_hub_resource_id|eventHubResourceId|
|**--consumer-group**|string|The event hub consumer group.|event_grid_consumer_group|consumerGroup|
|**--table-name**|string|The table where the data should be ingested. Optionally the table information can be added to each message.|event_grid_table_name|tableName|
|**--mapping-rule-name**|string|The mapping rule to be used to ingest the data. Optionally the mapping information can be added to each message.|event_grid_mapping_rule_name|mappingRuleName|
|**--data-format**|choice|The data format of the message. Optionally the data format can be added to each message.|event_grid_data_format|dataFormat|
|**--ignore-first-record**|boolean|A Boolean value that, if set to true, indicates that ingestion should ignore the first record of every file|event_grid_ignore_first_record|ignoreFirstRecord|
|**--blob-storage-event-type**|choice|The name of blob storage event type to process.|event_grid_blob_storage_event_type|blobStorageEventType|

#### <a name="KustoPoolDataConnectionsUpdate#EventHub">Command `az synapse kusto data-connection event-hub update`</a>

##### <a name="ExamplesKustoPoolDataConnectionsUpdate#EventHub">Example</a>
```
az synapse kusto data-connection event-hub update --data-connection-name "DataConnections8" --database-name \
"KustoDatabase8" --kusto-pool-name "kustoclusterrptest4" --location "westus" --consumer-group "testConsumerGroup1" \
--event-hub-resource-id "/subscriptions/12345678-1234-1234-1234-123456789098/resourceGroups/kustorptest/providers/Micro\
soft.EventHub/namespaces/eventhubTestns1/eventhubs/eventhubTest1" --resource-group "kustorptest" --workspace-name \
"synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDataConnectionsUpdate#EventHub">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--data-connection-name**|string|The name of the data connection.|data_connection_name|dataConnectionName|
|**--location**|string|Resource location.|event_hub_location|location|
|**--event-hub-resource-id**|string|The resource ID of the event hub to be used to create a data connection.|event_hub_event_hub_resource_id|eventHubResourceId|
|**--consumer-group**|string|The event hub consumer group.|event_hub_consumer_group|consumerGroup|
|**--table-name**|string|The table where the data should be ingested. Optionally the table information can be added to each message.|event_hub_table_name|tableName|
|**--mapping-rule-name**|string|The mapping rule to be used to ingest the data. Optionally the mapping information can be added to each message.|event_hub_mapping_rule_name|mappingRuleName|
|**--data-format**|choice|The data format of the message. Optionally the data format can be added to each message.|event_hub_data_format|dataFormat|
|**--event-system-properties**|array|System properties of the event hub|event_hub_event_system_properties|eventSystemProperties|
|**--compression**|choice|The event hub messages compression type|event_hub_compression|compression|
|**--managed-identity-resource-id**|string|The resource ID of a managed identity (system or user assigned) to be used to authenticate with event hub.|event_hub_managed_identity_resource_id|managedIdentityResourceId|

#### <a name="KustoPoolDataConnectionsUpdate#IotHub">Command `az synapse kusto data-connection iot-hub update`</a>


##### <a name="ParametersKustoPoolDataConnectionsUpdate#IotHub">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--data-connection-name**|string|The name of the data connection.|data_connection_name|dataConnectionName|
|**--location**|string|Resource location.|iot_hub_location|location|
|**--iot-hub-resource-id**|string|The resource ID of the Iot hub to be used to create a data connection.|iot_hub_iot_hub_resource_id|iotHubResourceId|
|**--consumer-group**|string|The iot hub consumer group.|iot_hub_consumer_group|consumerGroup|
|**--table-name**|string|The table where the data should be ingested. Optionally the table information can be added to each message.|iot_hub_table_name|tableName|
|**--mapping-rule-name**|string|The mapping rule to be used to ingest the data. Optionally the mapping information can be added to each message.|iot_hub_mapping_rule_name|mappingRuleName|
|**--data-format**|choice|The data format of the message. Optionally the data format can be added to each message.|iot_hub_data_format|dataFormat|
|**--event-system-properties**|array|System properties of the iot hub|iot_hub_event_system_properties|eventSystemProperties|
|**--shared-access-policy-name**|string|The name of the share access policy|iot_hub_shared_access_policy_name|sharedAccessPolicyName|

#### <a name="KustoPoolDataConnectionsDelete">Command `az synapse kusto data-connection delete`</a>

##### <a name="ExamplesKustoPoolDataConnectionsDelete">Example</a>
```
az synapse kusto data-connection delete --data-connection-name "kustoeventhubconnection1" --database-name \
"KustoDatabase8" --kusto-pool-name "kustoclusterrptest4" --resource-group "kustorptest" --workspace-name \
"synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDataConnectionsDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--data-connection-name**|string|The name of the data connection.|data_connection_name|dataConnectionName|

### group `az synapse kusto database`
#### <a name="KustoPoolDatabasesListByKustoPool">Command `az synapse kusto database list`</a>

##### <a name="ExamplesKustoPoolDatabasesListByKustoPool">Example</a>
```
az synapse kusto database list --kusto-pool-name "kustoclusterrptest4" --resource-group "kustorptest" --workspace-name \
"synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDatabasesListByKustoPool">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|

#### <a name="KustoPoolDatabasesGet">Command `az synapse kusto database show`</a>

##### <a name="ExamplesKustoPoolDatabasesGet">Example</a>
```
az synapse kusto database show --database-name "KustoDatabase8" --kusto-pool-name "kustoclusterrptest4" \
--resource-group "kustorptest" --workspace-name "synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDatabasesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|

#### <a name="KustoPoolDatabasesCreateOrUpdate#Create">Command `az synapse kusto database create`</a>

##### <a name="ExamplesKustoPoolDatabasesCreateOrUpdate#Create">Example</a>
```
az synapse kusto database create --database-name "KustoDatabase8" --kusto-pool-name "kustoclusterrptest4" \
--read-write-database location="westus" soft-delete-period="P1D" --resource-group "kustorptest" --workspace-name \
"synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDatabasesCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--read-write-database**|object|Class representing a read write database.|read_write_database|ReadWriteDatabase|

#### <a name="KustoPoolDatabasesUpdate">Command `az synapse kusto database update`</a>

##### <a name="ExamplesKustoPoolDatabasesUpdate">Example</a>
```
az synapse kusto database update --database-name "KustoDatabase8" --kusto-pool-name "kustoclusterrptest4" \
--read-write-database soft-delete-period="P1D" --resource-group "kustorptest" --workspace-name "synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDatabasesUpdate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--read-write-database**|object|Class representing a read write database.|read_write_database|ReadWriteDatabase|

#### <a name="KustoPoolDatabasesDelete">Command `az synapse kusto database delete`</a>

##### <a name="ExamplesKustoPoolDatabasesDelete">Example</a>
```
az synapse kusto database delete --database-name "KustoDatabase8" --kusto-pool-name "kustoclusterrptest4" \
--resource-group "kustorptest" --workspace-name "synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDatabasesDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|

### group `az synapse kusto database-principal-assignment`
#### <a name="KustoPoolDatabasePrincipalAssignmentsList">Command `az synapse kusto database-principal-assignment list`</a>

##### <a name="ExamplesKustoPoolDatabasePrincipalAssignmentsList">Example</a>
```
az synapse kusto database-principal-assignment list --database-name "Kustodatabase8" --kusto-pool-name \
"kustoclusterrptest4" --resource-group "kustorptest" --workspace-name "synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDatabasePrincipalAssignmentsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

#### <a name="KustoPoolDatabasePrincipalAssignmentsGet">Command `az synapse kusto database-principal-assignment show`</a>

##### <a name="ExamplesKustoPoolDatabasePrincipalAssignmentsGet">Example</a>
```
az synapse kusto database-principal-assignment show --database-name "Kustodatabase8" --kusto-pool-name \
"kustoclusterrptest4" --principal-assignment-name "kustoprincipal1" --resource-group "kustorptest" --workspace-name \
"synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDatabasePrincipalAssignmentsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--principal-assignment-name**|string|The name of the Kusto principalAssignment.|principal_assignment_name|principalAssignmentName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

#### <a name="KustoPoolDatabasePrincipalAssignmentsCreateOrUpdate#Create">Command `az synapse kusto database-principal-assignment create`</a>

##### <a name="ExamplesKustoPoolDatabasePrincipalAssignmentsCreateOrUpdate#Create">Example</a>
```
az synapse kusto database-principal-assignment create --database-name "Kustodatabase8" --kusto-pool-name \
"kustoclusterrptest4" --principal-id "87654321-1234-1234-1234-123456789123" --principal-type "App" --role "Admin" \
--tenant-id "12345678-1234-1234-1234-123456789123" --principal-assignment-name "kustoprincipal1" --resource-group \
"kustorptest" --workspace-name "synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDatabasePrincipalAssignmentsCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--principal-assignment-name**|string|The name of the Kusto principalAssignment.|principal_assignment_name|principalAssignmentName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--principal-id**|string|The principal ID assigned to the database principal. It can be a user email, application ID, or security group name.|principal_id|principalId|
|**--role**|choice|Database principal role.|role|role|
|**--tenant-id**|string|The tenant id of the principal|tenant_id|tenantId|
|**--principal-type**|choice|Principal type.|principal_type|principalType|

#### <a name="KustoPoolDatabasePrincipalAssignmentsCreateOrUpdate#Update">Command `az synapse kusto database-principal-assignment update`</a>


##### <a name="ParametersKustoPoolDatabasePrincipalAssignmentsCreateOrUpdate#Update">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--principal-assignment-name**|string|The name of the Kusto principalAssignment.|principal_assignment_name|principalAssignmentName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--principal-id**|string|The principal ID assigned to the database principal. It can be a user email, application ID, or security group name.|principal_id|principalId|
|**--role**|choice|Database principal role.|role|role|
|**--tenant-id**|string|The tenant id of the principal|tenant_id|tenantId|
|**--principal-type**|choice|Principal type.|principal_type|principalType|

#### <a name="KustoPoolDatabasePrincipalAssignmentsDelete">Command `az synapse kusto database-principal-assignment delete`</a>

##### <a name="ExamplesKustoPoolDatabasePrincipalAssignmentsDelete">Example</a>
```
az synapse kusto database-principal-assignment delete --database-name "Kustodatabase8" --kusto-pool-name \
"kustoclusterrptest4" --principal-assignment-name "kustoprincipal1" --resource-group "kustorptest" --workspace-name \
"synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolDatabasePrincipalAssignmentsDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--database-name**|string|The name of the database in the Kusto pool.|database_name|databaseName|
|**--principal-assignment-name**|string|The name of the Kusto principalAssignment.|principal_assignment_name|principalAssignmentName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

### group `az synapse kusto pool`
#### <a name="KustoPoolListSkus">Command `az synapse kusto pool list-sku`</a>

##### <a name="ExamplesKustoPoolListSkus">Example</a>
```
az synapse kusto pool list-sku
```
##### <a name="ParametersKustoPoolListSkus">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|

### group `az synapse kusto pool`
#### <a name="KustoPoolsListByWorkspace">Command `az synapse kusto pool list`</a>

##### <a name="ExamplesKustoPoolsListByWorkspace">Example</a>
```
az synapse kusto pool list --resource-group "kustorptest" --workspace-name "kustorptest"
```
##### <a name="ParametersKustoPoolsListByWorkspace">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

#### <a name="KustoPoolsGet">Command `az synapse kusto pool show`</a>

##### <a name="ExamplesKustoPoolsGet">Example</a>
```
az synapse kusto pool show --name "kustoclusterrptest4" --resource-group "kustorptest" --workspace-name \
"synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

#### <a name="KustoPoolsDelete">Command `az synapse kusto pool delete`</a>

##### <a name="ExamplesKustoPoolsDelete">Example</a>
```
az synapse kusto pool delete --name "kustoclusterrptest4" --resource-group "kustorptest" --workspace-name \
"kustorptest"
```
##### <a name="ParametersKustoPoolsDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|

#### <a name="KustoPoolsListFollowerDatabases">Command `az synapse kusto pool list-follower-database`</a>

##### <a name="ExamplesKustoPoolsListFollowerDatabases">Example</a>
```
az synapse kusto pool list-follower-database --name "kustoclusterrptest4" --resource-group "kustorptest" \
--workspace-name "kustorptest"
```
##### <a name="ParametersKustoPoolsListFollowerDatabases">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

#### <a name="KustoPoolsListLanguageExtensions">Command `az synapse kusto pool list-language-extension`</a>

##### <a name="ExamplesKustoPoolsListLanguageExtensions">Example</a>
```
az synapse kusto pool list-language-extension --name "kustoclusterrptest4" --resource-group "kustorptest" \
--workspace-name "kustorptest"
```
##### <a name="ParametersKustoPoolsListLanguageExtensions">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

#### <a name="KustoPoolsListSkusByResource">Command `az synapse kusto pool list-sku`</a>

##### <a name="ExamplesKustoPoolsListSkusByResource">Example</a>
```
az synapse kusto pool list-sku --name "kustoclusterrptest4" --resource-group "kustorptest" --workspace-name \
"synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolsListSkusByResource">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

#### <a name="KustoPoolsStart">Command `az synapse kusto pool start`</a>

##### <a name="ExamplesKustoPoolsStart">Example</a>
```
az synapse kusto pool start --name "kustoclusterrptest4" --resource-group "kustorptest" --workspace-name "kustorptest"
```
##### <a name="ParametersKustoPoolsStart">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

#### <a name="KustoPoolsStop">Command `az synapse kusto pool stop`</a>

##### <a name="ExamplesKustoPoolsStop">Example</a>
```
az synapse kusto pool stop --name "kustoclusterrptest4" --resource-group "kustorptest" --workspace-name "kustorptest"
```
##### <a name="ParametersKustoPoolsStop">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

### group `az synapse kusto pool-principal-assignment`
#### <a name="KustoPoolPrincipalAssignmentsList">Command `az synapse kusto pool-principal-assignment list`</a>

##### <a name="ExamplesKustoPoolPrincipalAssignmentsList">Example</a>
```
az synapse kusto pool-principal-assignment list --kusto-pool-name "kustoclusterrptest4" --resource-group "kustorptest" \
--workspace-name "synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolPrincipalAssignmentsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

#### <a name="KustoPoolPrincipalAssignmentsGet">Command `az synapse kusto pool-principal-assignment show`</a>

##### <a name="ExamplesKustoPoolPrincipalAssignmentsGet">Example</a>
```
az synapse kusto pool-principal-assignment show --kusto-pool-name "kustoclusterrptest4" --principal-assignment-name \
"kustoprincipal1" --resource-group "kustorptest" --workspace-name "synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolPrincipalAssignmentsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--principal-assignment-name**|string|The name of the Kusto principalAssignment.|principal_assignment_name|principalAssignmentName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

#### <a name="KustoPoolPrincipalAssignmentsCreateOrUpdate#Create">Command `az synapse kusto pool-principal-assignment create`</a>

##### <a name="ExamplesKustoPoolPrincipalAssignmentsCreateOrUpdate#Create">Example</a>
```
az synapse kusto pool-principal-assignment create --kusto-pool-name "kustoclusterrptest4" --principal-id \
"87654321-1234-1234-1234-123456789123" --principal-type "App" --role "AllDatabasesAdmin" --tenant-id \
"12345678-1234-1234-1234-123456789123" --principal-assignment-name "kustoprincipal1" --resource-group "kustorptest" \
--workspace-name "synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolPrincipalAssignmentsCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--principal-assignment-name**|string|The name of the Kusto principalAssignment.|principal_assignment_name|principalAssignmentName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--principal-id**|string|The principal ID assigned to the cluster principal. It can be a user email, application ID, or security group name.|principal_id|principalId|
|**--role**|choice|Cluster principal role.|role|role|
|**--tenant-id**|string|The tenant id of the principal|tenant_id|tenantId|
|**--principal-type**|choice|Principal type.|principal_type|principalType|

#### <a name="KustoPoolPrincipalAssignmentsCreateOrUpdate#Update">Command `az synapse kusto pool-principal-assignment update`</a>


##### <a name="ParametersKustoPoolPrincipalAssignmentsCreateOrUpdate#Update">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--principal-assignment-name**|string|The name of the Kusto principalAssignment.|principal_assignment_name|principalAssignmentName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--principal-id**|string|The principal ID assigned to the cluster principal. It can be a user email, application ID, or security group name.|principal_id|principalId|
|**--role**|choice|Cluster principal role.|role|role|
|**--tenant-id**|string|The tenant id of the principal|tenant_id|tenantId|
|**--principal-type**|choice|Principal type.|principal_type|principalType|

#### <a name="KustoPoolPrincipalAssignmentsDelete">Command `az synapse kusto pool-principal-assignment delete`</a>

##### <a name="ExamplesKustoPoolPrincipalAssignmentsDelete">Example</a>
```
az synapse kusto pool-principal-assignment delete --kusto-pool-name "kustoclusterrptest4" --principal-assignment-name \
"kustoprincipal1" --resource-group "kustorptest" --workspace-name "synapseWorkspaceName"
```
##### <a name="ParametersKustoPoolPrincipalAssignmentsDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--kusto-pool-name**|string|The name of the Kusto pool.|kusto_pool_name|kustoPoolName|
|**--principal-assignment-name**|string|The name of the Kusto principalAssignment.|principal_assignment_name|principalAssignmentName|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

### group `az synapse kusto-operation`
#### <a name="KustoOperationsList">Command `az synapse kusto-operation list`</a>

##### <a name="ExamplesKustoOperationsList">Example</a>
```
az synapse kusto-operation list
```
##### <a name="ParametersKustoOperationsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
