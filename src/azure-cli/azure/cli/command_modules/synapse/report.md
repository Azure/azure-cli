# Azure CLI Module Creation Report

### synapse big-data-pool create

create a synapse big-data-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse big-data-pool|BigDataPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--big-data-pool-name**|string|Big Data pool name|big_data_pool_name|bigDataPoolName|
|**--location**|string|The geo-location where the resource lives|location|location|
|**--force**|boolean|Whether to stop any running jobs in the Big Data pool|force|force|
|**--tags**|dictionary|Resource tags.|tags|tags|
|**--provisioning-state**|string|The state of the Big Data pool.|provisioning_state|provisioningState|
|**--auto-scale**|object|Auto-scaling properties|auto_scale|autoScale|
|**--creation-date**|date-time|The time when the Big Data pool was created.|creation_date|creationDate|
|**--auto-pause**|object|Auto-pausing properties|auto_pause|autoPause|
|**--spark-events-folder**|string|The Spark events folder|spark_events_folder|sparkEventsFolder|
|**--node-count**|integer|The number of nodes in the Big Data pool.|node_count|nodeCount|
|**--library-requirements**|object|Library version requirements|library_requirements|libraryRequirements|
|**--spark-version**|string|The Apache Spark version.|spark_version|sparkVersion|
|**--default-spark-log-folder**|string|The default folder where Spark logs will be written.|default_spark_log_folder|defaultSparkLogFolder|
|**--node-size**|choice|The level of compute power that each node in the Big Data pool has.|node_size|nodeSize|
|**--node-size-family**|choice|The kind of nodes that the Big Data pool provides.|node_size_family|nodeSizeFamily|

### synapse big-data-pool delete

delete a synapse big-data-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse big-data-pool|BigDataPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--big-data-pool-name**|string|Big Data pool name|big_data_pool_name|bigDataPoolName|

### synapse big-data-pool list

list a synapse big-data-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse big-data-pool|BigDataPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|ListByWorkspace|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

### synapse big-data-pool show

show a synapse big-data-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse big-data-pool|BigDataPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--big-data-pool-name**|string|Big Data pool name|big_data_pool_name|bigDataPoolName|

### synapse big-data-pool update

update a synapse big-data-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse big-data-pool|BigDataPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--big-data-pool-name**|string|Big Data pool name|big_data_pool_name|bigDataPoolName|
|**--tags**|dictionary|Updated tags for the Big Data pool|tags|tags|

### synapse integration-runtime create

create a synapse integration-runtime.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime|IntegrationRuntimes|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|
|**--properties**|object|Integration runtime properties.|properties|properties|
|**--if-match**|string|ETag of the integration runtime entity. Should only be specified for update, for which it should match existing entity or can be * for unconditional update.|if_match|If-Match|

### synapse integration-runtime delete

delete a synapse integration-runtime.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime|IntegrationRuntimes|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|

### synapse integration-runtime list

list a synapse integration-runtime.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime|IntegrationRuntimes|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|ListByWorkspace|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

### synapse integration-runtime show

show a synapse integration-runtime.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime|IntegrationRuntimes|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|
|**--if-none-match**|string|ETag of the integration runtime entity. Should only be specified for get. If the ETag matches the existing entity tag, or if * was provided, then no content will be returned.|if_none_match|If-None-Match|

### synapse integration-runtime start

start a synapse integration-runtime.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime|IntegrationRuntimes|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|start|Start|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|

### synapse integration-runtime stop

stop a synapse integration-runtime.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime|IntegrationRuntimes|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|stop|Stop|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|

### synapse integration-runtime update

update a synapse integration-runtime.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime|IntegrationRuntimes|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|
|**--auto-update**|choice|Enables or disables the auto-update feature of the self-hosted integration runtime. See https://go.microsoft.com/fwlink/?linkid=854189.|auto_update|autoUpdate|
|**--update-delay-offset**|string|The time offset (in hours) in the day, e.g., PT03H is 3 hours. The integration runtime auto update will happen on that time.|update_delay_offset|updateDelayOffset|

### synapse integration-runtime upgrade

upgrade a synapse integration-runtime.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime|IntegrationRuntimes|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|upgrade|Upgrade|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|

### synapse integration-runtime-auth-key list

list a synapse integration-runtime-auth-key.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-auth-key|IntegrationRuntimeAuthKeys|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|

### synapse integration-runtime-auth-key regenerate

regenerate a synapse integration-runtime-auth-key.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-auth-key|IntegrationRuntimeAuthKeys|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|regenerate|Regenerate|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|
|**--key-name**|choice|The name of the authentication key to regenerate.|key_name|keyName|

### synapse integration-runtime-connection-info get

get a synapse integration-runtime-connection-info.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-connection-info|IntegrationRuntimeConnectionInfos|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|get|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|

### synapse integration-runtime-credentials sync

sync a synapse integration-runtime-credentials.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-credentials|IntegrationRuntimeCredentials|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|sync|Sync|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|

### synapse integration-runtime-monitoring-data get

get a synapse integration-runtime-monitoring-data.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-monitoring-data|IntegrationRuntimeMonitoringData|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|get|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|

### synapse integration-runtime-node delete

delete a synapse integration-runtime-node.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-node|IntegrationRuntimeNodes|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|
|**--node-name**|string|Integration runtime node name|node_name|nodeName|

### synapse integration-runtime-node show

show a synapse integration-runtime-node.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-node|IntegrationRuntimeNodes|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|
|**--node-name**|string|Integration runtime node name|node_name|nodeName|

### synapse integration-runtime-node update

update a synapse integration-runtime-node.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-node|IntegrationRuntimeNodes|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|
|**--node-name**|string|Integration runtime node name|node_name|nodeName|
|**--concurrent-jobs-limit**|integer|The number of concurrent jobs permitted to run on the integration runtime node. Values between 1 and maxConcurrentJobs(inclusive) are allowed.|concurrent_jobs_limit|concurrentJobsLimit|

### synapse integration-runtime-node-ip-address get

get a synapse integration-runtime-node-ip-address.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-node-ip-address|IntegrationRuntimeNodeIpAddress|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|get|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|
|**--node-name**|string|Integration runtime node name|node_name|nodeName|

### synapse integration-runtime-object-metadata get

get a synapse integration-runtime-object-metadata.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-object-metadata|IntegrationRuntimeObjectMetadata|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|get|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|
|**--metadata-path**|string|Metadata path.|metadata_path|metadataPath|

### synapse integration-runtime-object-metadata refresh

refresh a synapse integration-runtime-object-metadata.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-object-metadata|IntegrationRuntimeObjectMetadata|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|refresh|Refresh|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|

### synapse integration-runtime-status get

get a synapse integration-runtime-status.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse integration-runtime-status|IntegrationRuntimeStatus|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|get|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--integration-runtime-name**|string|Integration runtime name|integration_runtime_name|integrationRuntimeName|

### synapse ip-firewall-rule create

create a synapse ip-firewall-rule.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse ip-firewall-rule|IpFirewallRules|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--rule-name**|string|The IP firewall rule name|rule_name|ruleName|
|**--end-ip-address**|string|The end IP address of the firewall rule. Must be IPv4 format. Must be greater than or equal to startIpAddress|end_ip_address|endIpAddress|
|**--start-ip-address**|string|The start IP address of the firewall rule. Must be IPv4 format|start_ip_address|startIpAddress|

### synapse ip-firewall-rule delete

delete a synapse ip-firewall-rule.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse ip-firewall-rule|IpFirewallRules|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--rule-name**|string|The IP firewall rule name|rule_name|ruleName|

### synapse ip-firewall-rule list

list a synapse ip-firewall-rule.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse ip-firewall-rule|IpFirewallRules|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|ListByWorkspace|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

### synapse ip-firewall-rule replace-all

replace-all a synapse ip-firewall-rule.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse ip-firewall-rule|IpFirewallRules|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|replace-all|ReplaceAll|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--ip-firewall-rules**|dictionary|IP firewall rule properties|ip_firewall_rules|ipFirewallRules|

### synapse ip-firewall-rule show

show a synapse ip-firewall-rule.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse ip-firewall-rule|IpFirewallRules|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--rule-name**|string|The IP firewall rule name|rule_name|ruleName|

### synapse ip-firewall-rule update

update a synapse ip-firewall-rule.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse ip-firewall-rule|IpFirewallRules|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|CreateOrUpdate#Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--rule-name**|string|The IP firewall rule name|rule_name|ruleName|
|**--end-ip-address**|string|The end IP address of the firewall rule. Must be IPv4 format. Must be greater than or equal to startIpAddress|end_ip_address|endIpAddress|
|**--start-ip-address**|string|The start IP address of the firewall rule. Must be IPv4 format|start_ip_address|startIpAddress|

### synapse operation get-azure-async-header-result

get-azure-async-header-result a synapse operation.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse operation|Operations|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|get-azure-async-header-result|GetAzureAsyncHeaderResult|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--operation-id**|string|Operation ID|operation_id|operationId|

### synapse operation get-location-header-result

get-location-header-result a synapse operation.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse operation|Operations|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|get-location-header-result|GetLocationHeaderResult|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--operation-id**|string|Operation ID|operation_id|operationId|

### synapse private-endpoint-connection create

create a synapse private-endpoint-connection.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse private-endpoint-connection|PrivateEndpointConnections|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--private-endpoint-connection-name**|string|The name of the private endpoint connection.|private_endpoint_connection_name|privateEndpointConnectionName|

### synapse private-endpoint-connection delete

delete a synapse private-endpoint-connection.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse private-endpoint-connection|PrivateEndpointConnections|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--private-endpoint-connection-name**|string|The name of the private endpoint connection.|private_endpoint_connection_name|privateEndpointConnectionName|

### synapse private-endpoint-connection list

list a synapse private-endpoint-connection.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse private-endpoint-connection|PrivateEndpointConnections|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

### synapse private-endpoint-connection show

show a synapse private-endpoint-connection.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse private-endpoint-connection|PrivateEndpointConnections|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--private-endpoint-connection-name**|string|The name of the private endpoint connection.|private_endpoint_connection_name|privateEndpointConnectionName|

### synapse private-link-hub create

create a synapse private-link-hub.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse private-link-hub|PrivateLinkHubs|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--private-link-hub-name**|string|The name of the privateLinkHub|private_link_hub_name|privateLinkHubName|
|**--location**|string|The geo-location where the resource lives|location|location|
|**--tags**|dictionary|Resource tags.|tags|tags|

### synapse private-link-hub delete

delete a synapse private-link-hub.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse private-link-hub|PrivateLinkHubs|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--private-link-hub-name**|string|The name of the privateLinkHub|private_link_hub_name|privateLinkHubName|

### synapse private-link-hub list

list a synapse private-link-hub.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse private-link-hub|PrivateLinkHubs|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|ListByResourceGroup|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

### synapse private-link-hub show

show a synapse private-link-hub.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse private-link-hub|PrivateLinkHubs|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--private-link-hub-name**|string|The name of the privateLinkHub|private_link_hub_name|privateLinkHubName|

### synapse private-link-hub update

update a synapse private-link-hub.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse private-link-hub|PrivateLinkHubs|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--private-link-hub-name**|string|The name of the privateLinkHub|private_link_hub_name|privateLinkHubName|
|**--tags**|dictionary|Resource tags|tags|tags|

### synapse private-link-resource list

list a synapse private-link-resource.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse private-link-resource|PrivateLinkResources|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

### synapse private-link-resource show

show a synapse private-link-resource.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse private-link-resource|PrivateLinkResources|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--private-link-resource-name**|string|The name of the private link resource|private_link_resource_name|privateLinkResourceName|

### synapse s-q-l-pool create

create a synapse s-q-l-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool|SqlPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--location**|string|The geo-location where the resource lives|location|location|
|**--tags**|dictionary|Resource tags.|tags|tags|
|**--sku**|object|SQL pool SKU|sku|sku|
|**--max-size-bytes**|integer|Maximum size in bytes|max_size_bytes|maxSizeBytes|
|**--collation**|string|Collation mode|collation|collation|
|**--source-database-id**|string|Source database to create from|source_database_id|sourceDatabaseId|
|**--recoverable-database-id**|string|Backup database to restore from|recoverable_database_id|recoverableDatabaseId|
|**--provisioning-state**|string|Resource state|provisioning_state|provisioningState|
|**--status**|string|Resource status|status|status|
|**--restore-point-in-time**|date-time|Snapshot time to restore|restore_point_in_time|restorePointInTime|
|**--create-mode**|string|What is this?|create_mode|createMode|
|**--creation-date**|date-time|Date the SQL pool was created|creation_date|creationDate|

### synapse s-q-l-pool delete

delete a synapse s-q-l-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool|SqlPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool list

list a synapse s-q-l-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool|SqlPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|ListByWorkspace|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

### synapse s-q-l-pool pause

pause a synapse s-q-l-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool|SqlPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|pause|Pause|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool rename

rename a synapse s-q-l-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool|SqlPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|rename|Rename|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--id**|string|The target ID for the resource|id|id|

### synapse s-q-l-pool resume

resume a synapse s-q-l-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool|SqlPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|resume|Resume|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool show

show a synapse s-q-l-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool|SqlPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool update

update a synapse s-q-l-pool.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool|SqlPools|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--tags**|dictionary|Resource tags.|tags|tags|
|**--location**|string|The geo-location where the resource lives|location|location|
|**--sku**|object|SQL pool SKU|sku|sku|
|**--max-size-bytes**|integer|Maximum size in bytes|max_size_bytes|maxSizeBytes|
|**--collation**|string|Collation mode|collation|collation|
|**--source-database-id**|string|Source database to create from|source_database_id|sourceDatabaseId|
|**--recoverable-database-id**|string|Backup database to restore from|recoverable_database_id|recoverableDatabaseId|
|**--provisioning-state**|string|Resource state|provisioning_state|provisioningState|
|**--status**|string|Resource status|status|status|
|**--restore-point-in-time**|date-time|Snapshot time to restore|restore_point_in_time|restorePointInTime|
|**--create-mode**|string|What is this?|create_mode|createMode|
|**--creation-date**|date-time|Date the SQL pool was created|creation_date|creationDate|

### synapse s-q-l-pool-blob-auditing-policy create

create a synapse s-q-l-pool-blob-auditing-policy.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-blob-auditing-policy|SqlPoolBlobAuditingPolicies|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--state**|sealed-choice|Specifies the state of the policy. If state is Enabled, storageEndpoint or isAzureMonitorTargetEnabled are required.|state|state|
|**--storage-endpoint**|string|Specifies the blob storage endpoint (e.g. https://MyAccount.blob.core.windows.net). If state is Enabled, storageEndpoint is required.|storage_endpoint|storageEndpoint|
|**--storage-account-access-key**|string|Specifies the identifier key of the auditing storage account. If state is Enabled and storageEndpoint is specified, storageAccountAccessKey is required.|storage_account_access_key|storageAccountAccessKey|
|**--retention-days**|integer|Specifies the number of days to keep in the audit logs in the storage account.|retention_days|retentionDays|
|**--audit-actions-and-groups**|array|Specifies the Actions-Groups and Actions to audit.  The recommended set of action groups to use is the following combination - this will audit all the queries and stored procedures executed against the database, as well as successful and failed logins:  BATCH_COMPLETED_GROUP, SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP, FAILED_DATABASE_AUTHENTICATION_GROUP.  This above combination is also the set that is configured by default when enabling auditing from the Azure portal.  The supported action groups to audit are (note: choose only specific groups that cover your auditing needs. Using unnecessary groups could lead to very large quantities of audit records):  APPLICATION_ROLE_CHANGE_PASSWORD_GROUP BACKUP_RESTORE_GROUP DATABASE_LOGOUT_GROUP DATABASE_OBJECT_CHANGE_GROUP DATABASE_OBJECT_OWNERSHIP_CHANGE_GROUP DATABASE_OBJECT_PERMISSION_CHANGE_GROUP DATABASE_OPERATION_GROUP DATABASE_PERMISSION_CHANGE_GROUP DATABASE_PRINCIPAL_CHANGE_GROUP DATABASE_PRINCIPAL_IMPERSONATION_GROUP DATABASE_ROLE_MEMBER_CHANGE_GROUP FAILED_DATABASE_AUTHENTICATION_GROUP SCHEMA_OBJECT_ACCESS_GROUP SCHEMA_OBJECT_CHANGE_GROUP SCHEMA_OBJECT_OWNERSHIP_CHANGE_GROUP SCHEMA_OBJECT_PERMISSION_CHANGE_GROUP SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP USER_CHANGE_PASSWORD_GROUP BATCH_STARTED_GROUP BATCH_COMPLETED_GROUP  These are groups that cover all sql statements and stored procedures executed against the database, and should not be used in combination with other groups as this will result in duplicate audit logs.  For more information, see [Database-Level Audit Action Groups](https://docs.microsoft.com/en-us/sql/relational-databases/security/auditing/sql-server-audit-action-groups-and-actions#database-level-audit-action-groups).  For Database auditing policy, specific Actions can also be specified (note that Actions cannot be specified for Server auditing policy). The supported actions to audit are: SELECT UPDATE INSERT DELETE EXECUTE RECEIVE REFERENCES  The general form for defining an action to be audited is: {action} ON {object} BY {principal}  Note that <object> in the above format can refer to an object like a table, view, or stored procedure, or an entire database or schema. For the latter cases, the forms DATABASE::{db_name} and SCHEMA::{schema_name} are used, respectively.  For example: SELECT on dbo.myTable by public SELECT on DATABASE::myDatabase by public SELECT on SCHEMA::mySchema by public  For more information, see [Database-Level Audit Actions](https://docs.microsoft.com/en-us/sql/relational-databases/security/auditing/sql-server-audit-action-groups-and-actions#database-level-audit-actions)|audit_actions_and_groups|auditActionsAndGroups|
|**--storage-account-subscription-id**|uuid|Specifies the blob storage subscription Id.|storage_account_subscription_id|storageAccountSubscriptionId|
|**--is-storage-secondary-key-in-use**|boolean|Specifies whether storageAccountAccessKey value is the storage's secondary key.|is_storage_secondary_key_in_use|isStorageSecondaryKeyInUse|
|**--is-azure-monitor-target-enabled**|boolean|Specifies whether audit events are sent to Azure Monitor.  In order to send the events to Azure Monitor, specify 'state' as 'Enabled' and 'isAzureMonitorTargetEnabled' as true.  When using REST API to configure auditing, Diagnostic Settings with 'SQLSecurityAuditEvents' diagnostic logs category on the database should be also created. Note that for server level audit you should use the 'master' database as {databaseName}.  Diagnostic Settings URI format: PUT https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.Sql/servers/{serverName}/databases/{databaseName}/providers/microsoft.insights/diagnosticSettings/{settingsName}?api-version=2017-05-01-preview  For more information, see [Diagnostic Settings REST API](https://go.microsoft.com/fwlink/?linkid=2033207) or [Diagnostic Settings PowerShell](https://go.microsoft.com/fwlink/?linkid=2033043) |is_azure_monitor_target_enabled|isAzureMonitorTargetEnabled|

### synapse s-q-l-pool-blob-auditing-policy show

show a synapse s-q-l-pool-blob-auditing-policy.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-blob-auditing-policy|SqlPoolBlobAuditingPolicies|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-blob-auditing-policy update

update a synapse s-q-l-pool-blob-auditing-policy.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-blob-auditing-policy|SqlPoolBlobAuditingPolicies|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|CreateOrUpdate#Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--state**|sealed-choice|Specifies the state of the policy. If state is Enabled, storageEndpoint or isAzureMonitorTargetEnabled are required.|state|state|
|**--storage-endpoint**|string|Specifies the blob storage endpoint (e.g. https://MyAccount.blob.core.windows.net). If state is Enabled, storageEndpoint is required.|storage_endpoint|storageEndpoint|
|**--storage-account-access-key**|string|Specifies the identifier key of the auditing storage account. If state is Enabled and storageEndpoint is specified, storageAccountAccessKey is required.|storage_account_access_key|storageAccountAccessKey|
|**--retention-days**|integer|Specifies the number of days to keep in the audit logs in the storage account.|retention_days|retentionDays|
|**--audit-actions-and-groups**|array|Specifies the Actions-Groups and Actions to audit.  The recommended set of action groups to use is the following combination - this will audit all the queries and stored procedures executed against the database, as well as successful and failed logins:  BATCH_COMPLETED_GROUP, SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP, FAILED_DATABASE_AUTHENTICATION_GROUP.  This above combination is also the set that is configured by default when enabling auditing from the Azure portal.  The supported action groups to audit are (note: choose only specific groups that cover your auditing needs. Using unnecessary groups could lead to very large quantities of audit records):  APPLICATION_ROLE_CHANGE_PASSWORD_GROUP BACKUP_RESTORE_GROUP DATABASE_LOGOUT_GROUP DATABASE_OBJECT_CHANGE_GROUP DATABASE_OBJECT_OWNERSHIP_CHANGE_GROUP DATABASE_OBJECT_PERMISSION_CHANGE_GROUP DATABASE_OPERATION_GROUP DATABASE_PERMISSION_CHANGE_GROUP DATABASE_PRINCIPAL_CHANGE_GROUP DATABASE_PRINCIPAL_IMPERSONATION_GROUP DATABASE_ROLE_MEMBER_CHANGE_GROUP FAILED_DATABASE_AUTHENTICATION_GROUP SCHEMA_OBJECT_ACCESS_GROUP SCHEMA_OBJECT_CHANGE_GROUP SCHEMA_OBJECT_OWNERSHIP_CHANGE_GROUP SCHEMA_OBJECT_PERMISSION_CHANGE_GROUP SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP USER_CHANGE_PASSWORD_GROUP BATCH_STARTED_GROUP BATCH_COMPLETED_GROUP  These are groups that cover all sql statements and stored procedures executed against the database, and should not be used in combination with other groups as this will result in duplicate audit logs.  For more information, see [Database-Level Audit Action Groups](https://docs.microsoft.com/en-us/sql/relational-databases/security/auditing/sql-server-audit-action-groups-and-actions#database-level-audit-action-groups).  For Database auditing policy, specific Actions can also be specified (note that Actions cannot be specified for Server auditing policy). The supported actions to audit are: SELECT UPDATE INSERT DELETE EXECUTE RECEIVE REFERENCES  The general form for defining an action to be audited is: {action} ON {object} BY {principal}  Note that <object> in the above format can refer to an object like a table, view, or stored procedure, or an entire database or schema. For the latter cases, the forms DATABASE::{db_name} and SCHEMA::{schema_name} are used, respectively.  For example: SELECT on dbo.myTable by public SELECT on DATABASE::myDatabase by public SELECT on SCHEMA::mySchema by public  For more information, see [Database-Level Audit Actions](https://docs.microsoft.com/en-us/sql/relational-databases/security/auditing/sql-server-audit-action-groups-and-actions#database-level-audit-actions)|audit_actions_and_groups|auditActionsAndGroups|
|**--storage-account-subscription-id**|uuid|Specifies the blob storage subscription Id.|storage_account_subscription_id|storageAccountSubscriptionId|
|**--is-storage-secondary-key-in-use**|boolean|Specifies whether storageAccountAccessKey value is the storage's secondary key.|is_storage_secondary_key_in_use|isStorageSecondaryKeyInUse|
|**--is-azure-monitor-target-enabled**|boolean|Specifies whether audit events are sent to Azure Monitor.  In order to send the events to Azure Monitor, specify 'state' as 'Enabled' and 'isAzureMonitorTargetEnabled' as true.  When using REST API to configure auditing, Diagnostic Settings with 'SQLSecurityAuditEvents' diagnostic logs category on the database should be also created. Note that for server level audit you should use the 'master' database as {databaseName}.  Diagnostic Settings URI format: PUT https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.Sql/servers/{serverName}/databases/{databaseName}/providers/microsoft.insights/diagnosticSettings/{settingsName}?api-version=2017-05-01-preview  For more information, see [Diagnostic Settings REST API](https://go.microsoft.com/fwlink/?linkid=2033207) or [Diagnostic Settings PowerShell](https://go.microsoft.com/fwlink/?linkid=2033043) |is_azure_monitor_target_enabled|isAzureMonitorTargetEnabled|

### synapse s-q-l-pool-connection-policy show

show a synapse s-q-l-pool-connection-policy.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-connection-policy|SqlPoolConnectionPolicies|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-data-warehouse-user-activity show

show a synapse s-q-l-pool-data-warehouse-user-activity.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-data-warehouse-user-activity|SqlPoolDataWarehouseUserActivities|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-geo-backup-policy show

show a synapse s-q-l-pool-geo-backup-policy.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-geo-backup-policy|SqlPoolGeoBackupPolicies|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-metadata-sync-config create

create a synapse s-q-l-pool-metadata-sync-config.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-metadata-sync-config|SqlPoolMetadataSyncConfigs|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--enabled**|boolean|Indicates whether the metadata sync is enabled or disabled|enabled|enabled|

### synapse s-q-l-pool-metadata-sync-config show

show a synapse s-q-l-pool-metadata-sync-config.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-metadata-sync-config|SqlPoolMetadataSyncConfigs|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-operation list

list a synapse s-q-l-pool-operation.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-operation|SqlPoolOperations|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-operation-result get-location-header-result

get-location-header-result a synapse s-q-l-pool-operation-result.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-operation-result|SqlPoolOperationResults|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|get-location-header-result|GetLocationHeaderResult|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--operation-id**|string|Operation ID|operation_id|operationId|

### synapse s-q-l-pool-replication-link list

list a synapse s-q-l-pool-replication-link.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-replication-link|SqlPoolReplicationLinks|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-restore-point create

create a synapse s-q-l-pool-restore-point.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-restore-point|SqlPoolRestorePoints|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--restore-point-label**|string|The restore point label to apply|restore_point_label|restorePointLabel|

### synapse s-q-l-pool-restore-point list

list a synapse s-q-l-pool-restore-point.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-restore-point|SqlPoolRestorePoints|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-schema list

list a synapse s-q-l-pool-schema.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-schema|SqlPoolSchemas|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--filter**|string|An OData filter expression that filters elements in the collection.|filter|$filter|

### synapse s-q-l-pool-security-alert-policy create

create a synapse s-q-l-pool-security-alert-policy.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-security-alert-policy|SqlPoolSecurityAlertPolicies|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--state**|sealed-choice|Specifies the state of the policy, whether it is enabled or disabled or a policy has not been applied yet on the specific Sql pool.|state|state|
|**--disabled-alerts**|array|Specifies an array of alerts that are disabled. Allowed values are: Sql_Injection, Sql_Injection_Vulnerability, Access_Anomaly, Data_Exfiltration, Unsafe_Action|disabled_alerts|disabledAlerts|
|**--email-addresses**|array|Specifies an array of e-mail addresses to which the alert is sent.|email_addresses|emailAddresses|
|**--email-account-admins**|boolean|Specifies that the alert is sent to the account administrators.|email_account_admins|emailAccountAdmins|
|**--storage-endpoint**|string|Specifies the blob storage endpoint (e.g. https://MyAccount.blob.core.windows.net). This blob storage will hold all Threat Detection audit logs.|storage_endpoint|storageEndpoint|
|**--storage-account-access-key**|string|Specifies the identifier key of the Threat Detection audit storage account.|storage_account_access_key|storageAccountAccessKey|
|**--retention-days**|integer|Specifies the number of days to keep in the Threat Detection audit logs.|retention_days|retentionDays|

### synapse s-q-l-pool-security-alert-policy show

show a synapse s-q-l-pool-security-alert-policy.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-security-alert-policy|SqlPoolSecurityAlertPolicies|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-security-alert-policy update

update a synapse s-q-l-pool-security-alert-policy.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-security-alert-policy|SqlPoolSecurityAlertPolicies|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|CreateOrUpdate#Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--state**|sealed-choice|Specifies the state of the policy, whether it is enabled or disabled or a policy has not been applied yet on the specific Sql pool.|state|state|
|**--disabled-alerts**|array|Specifies an array of alerts that are disabled. Allowed values are: Sql_Injection, Sql_Injection_Vulnerability, Access_Anomaly, Data_Exfiltration, Unsafe_Action|disabled_alerts|disabledAlerts|
|**--email-addresses**|array|Specifies an array of e-mail addresses to which the alert is sent.|email_addresses|emailAddresses|
|**--email-account-admins**|boolean|Specifies that the alert is sent to the account administrators.|email_account_admins|emailAccountAdmins|
|**--storage-endpoint**|string|Specifies the blob storage endpoint (e.g. https://MyAccount.blob.core.windows.net). This blob storage will hold all Threat Detection audit logs.|storage_endpoint|storageEndpoint|
|**--storage-account-access-key**|string|Specifies the identifier key of the Threat Detection audit storage account.|storage_account_access_key|storageAccountAccessKey|
|**--retention-days**|integer|Specifies the number of days to keep in the Threat Detection audit logs.|retention_days|retentionDays|

### synapse s-q-l-pool-sensitivity-label create

create a synapse s-q-l-pool-sensitivity-label.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-sensitivity-label|SqlPoolSensitivityLabels|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--schema-name**|string|The name of the schema.|schema_name|schemaName|
|**--table-name**|string|The name of the table.|table_name|tableName|
|**--column-name**|string|The name of the column.|column_name|columnName|
|**--label-name**|string|The label name.|label_name|labelName|
|**--label-id**|string|The label ID.|label_id|labelId|
|**--information-type**|string|The information type.|information_type|informationType|
|**--information-type-id**|string|The information type ID.|information_type_id|informationTypeId|

### synapse s-q-l-pool-sensitivity-label delete

delete a synapse s-q-l-pool-sensitivity-label.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-sensitivity-label|SqlPoolSensitivityLabels|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--schema-name**|string|The name of the schema.|schema_name|schemaName|
|**--table-name**|string|The name of the table.|table_name|tableName|
|**--column-name**|string|The name of the column.|column_name|columnName|

### synapse s-q-l-pool-sensitivity-label disable-recommendation

disable-recommendation a synapse s-q-l-pool-sensitivity-label.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-sensitivity-label|SqlPoolSensitivityLabels|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|disable-recommendation|DisableRecommendation|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--schema-name**|string|The name of the schema.|schema_name|schemaName|
|**--table-name**|string|The name of the table.|table_name|tableName|
|**--column-name**|string|The name of the column.|column_name|columnName|

### synapse s-q-l-pool-sensitivity-label enable-recommendation

enable-recommendation a synapse s-q-l-pool-sensitivity-label.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-sensitivity-label|SqlPoolSensitivityLabels|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|enable-recommendation|EnableRecommendation|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--schema-name**|string|The name of the schema.|schema_name|schemaName|
|**--table-name**|string|The name of the table.|table_name|tableName|
|**--column-name**|string|The name of the column.|column_name|columnName|

### synapse s-q-l-pool-sensitivity-label list-current

list-current a synapse s-q-l-pool-sensitivity-label.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-sensitivity-label|SqlPoolSensitivityLabels|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list-current|ListCurrent|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--filter**|string|An OData filter expression that filters elements in the collection.|filter|$filter|

### synapse s-q-l-pool-sensitivity-label list-recommended

list-recommended a synapse s-q-l-pool-sensitivity-label.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-sensitivity-label|SqlPoolSensitivityLabels|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list-recommended|ListRecommended|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--include-disabled-recommendations**|boolean|Specifies whether to include disabled recommendations or not.|include_disabled_recommendations|includeDisabledRecommendations|
|**--skip-token**|string|An OData query option to indicate how many elements to skip in the collection.|skip_token|$skipToken|
|**--filter**|string|An OData filter expression that filters elements in the collection.|filter|$filter|

### synapse s-q-l-pool-sensitivity-label update

update a synapse s-q-l-pool-sensitivity-label.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-sensitivity-label|SqlPoolSensitivityLabels|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|CreateOrUpdate#Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--schema-name**|string|The name of the schema.|schema_name|schemaName|
|**--table-name**|string|The name of the table.|table_name|tableName|
|**--column-name**|string|The name of the column.|column_name|columnName|
|**--label-name**|string|The label name.|label_name|labelName|
|**--label-id**|string|The label ID.|label_id|labelId|
|**--information-type**|string|The information type.|information_type|informationType|
|**--information-type-id**|string|The information type ID.|information_type_id|informationTypeId|

### synapse s-q-l-pool-table list

list a synapse s-q-l-pool-table.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-table|SqlPoolTables|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|ListBySchema|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--schema-name**|string|The name of the schema.|schema_name|schemaName|
|**--filter**|string|An OData filter expression that filters elements in the collection.|filter|$filter|

### synapse s-q-l-pool-table-column list

list a synapse s-q-l-pool-table-column.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-table-column|SqlPoolTableColumns|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|ListByTableName|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--schema-name**|string|The name of the schema.|schema_name|schemaName|
|**--table-name**|string|The name of the table.|table_name|tableName|
|**--filter**|string|An OData filter expression that filters elements in the collection.|filter|$filter|

### synapse s-q-l-pool-transparent-data-encryption create

create a synapse s-q-l-pool-transparent-data-encryption.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-transparent-data-encryption|SqlPoolTransparentDataEncryptions|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--status**|sealed-choice|The status of the database transparent data encryption.|status|status|

### synapse s-q-l-pool-transparent-data-encryption show

show a synapse s-q-l-pool-transparent-data-encryption.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-transparent-data-encryption|SqlPoolTransparentDataEncryptions|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-transparent-data-encryption update

update a synapse s-q-l-pool-transparent-data-encryption.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-transparent-data-encryption|SqlPoolTransparentDataEncryptions|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|CreateOrUpdate#Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--status**|sealed-choice|The status of the database transparent data encryption.|status|status|

### synapse s-q-l-pool-usage list

list a synapse s-q-l-pool-usage.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-usage|SqlPoolUsages|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-vulnerability-assessment create

create a synapse s-q-l-pool-vulnerability-assessment.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-vulnerability-assessment|SqlPoolVulnerabilityAssessments|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--storage-container-path**|string|A blob storage container path to hold the scan results (e.g. https://myStorage.blob.core.windows.net/VaScans/).  It is required if server level vulnerability assessment policy doesn't set|storage_container_path|storageContainerPath|
|**--storage-container-sas-key**|string|A shared access signature (SAS Key) that has write access to the blob container specified in 'storageContainerPath' parameter. If 'storageAccountAccessKey' isn't specified, StorageContainerSasKey is required.|storage_container_sas_key|storageContainerSasKey|
|**--storage-account-access-key**|string|Specifies the identifier key of the storage account for vulnerability assessment scan results. If 'StorageContainerSasKey' isn't specified, storageAccountAccessKey is required.|storage_account_access_key|storageAccountAccessKey|
|**--recurring-scans**|object|The recurring scans settings|recurring_scans|recurringScans|

### synapse s-q-l-pool-vulnerability-assessment delete

delete a synapse s-q-l-pool-vulnerability-assessment.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-vulnerability-assessment|SqlPoolVulnerabilityAssessments|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-vulnerability-assessment list

list a synapse s-q-l-pool-vulnerability-assessment.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-vulnerability-assessment|SqlPoolVulnerabilityAssessments|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-vulnerability-assessment show

show a synapse s-q-l-pool-vulnerability-assessment.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-vulnerability-assessment|SqlPoolVulnerabilityAssessments|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse s-q-l-pool-vulnerability-assessment update

update a synapse s-q-l-pool-vulnerability-assessment.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-vulnerability-assessment|SqlPoolVulnerabilityAssessments|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|CreateOrUpdate#Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--storage-container-path**|string|A blob storage container path to hold the scan results (e.g. https://myStorage.blob.core.windows.net/VaScans/).  It is required if server level vulnerability assessment policy doesn't set|storage_container_path|storageContainerPath|
|**--storage-container-sas-key**|string|A shared access signature (SAS Key) that has write access to the blob container specified in 'storageContainerPath' parameter. If 'storageAccountAccessKey' isn't specified, StorageContainerSasKey is required.|storage_container_sas_key|storageContainerSasKey|
|**--storage-account-access-key**|string|Specifies the identifier key of the storage account for vulnerability assessment scan results. If 'StorageContainerSasKey' isn't specified, storageAccountAccessKey is required.|storage_account_access_key|storageAccountAccessKey|
|**--recurring-scans**|object|The recurring scans settings|recurring_scans|recurringScans|

### synapse s-q-l-pool-vulnerability-assessment-rule-baseline create

create a synapse s-q-l-pool-vulnerability-assessment-rule-baseline.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-vulnerability-assessment-rule-baseline|SqlPoolVulnerabilityAssessmentRuleBaselines|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--rule-id**|string|The vulnerability assessment rule ID.|rule_id|ruleId|
|**--baseline-name**|sealed-choice|The name of the vulnerability assessment rule baseline (default implies a baseline on a Sql pool level rule and master for workspace level rule).|baseline_name|baselineName|
|**--baseline-results**|array|The rule baseline result|baseline_results|baselineResults|

### synapse s-q-l-pool-vulnerability-assessment-rule-baseline delete

delete a synapse s-q-l-pool-vulnerability-assessment-rule-baseline.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-vulnerability-assessment-rule-baseline|SqlPoolVulnerabilityAssessmentRuleBaselines|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--rule-id**|string|The vulnerability assessment rule ID.|rule_id|ruleId|
|**--baseline-name**|sealed-choice|The name of the vulnerability assessment rule baseline (default implies a baseline on a Sql pool level rule and master for workspace level rule).|baseline_name|baselineName|

### synapse s-q-l-pool-vulnerability-assessment-rule-baseline update

update a synapse s-q-l-pool-vulnerability-assessment-rule-baseline.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-vulnerability-assessment-rule-baseline|SqlPoolVulnerabilityAssessmentRuleBaselines|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|CreateOrUpdate#Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--rule-id**|string|The vulnerability assessment rule ID.|rule_id|ruleId|
|**--baseline-name**|sealed-choice|The name of the vulnerability assessment rule baseline (default implies a baseline on a Sql pool level rule and master for workspace level rule).|baseline_name|baselineName|
|**--baseline-results**|array|The rule baseline result|baseline_results|baselineResults|

### synapse s-q-l-pool-vulnerability-assessment-scan export

export a synapse s-q-l-pool-vulnerability-assessment-scan.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-vulnerability-assessment-scan|SqlPoolVulnerabilityAssessmentScans|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|export|Export|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--scan-id**|string|The vulnerability assessment scan Id of the scan to retrieve.|scan_id|scanId|

### synapse s-q-l-pool-vulnerability-assessment-scan initiate-scan

initiate-scan a synapse s-q-l-pool-vulnerability-assessment-scan.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-vulnerability-assessment-scan|SqlPoolVulnerabilityAssessmentScans|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|initiate-scan|InitiateScan|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|
|**--scan-id**|string|The vulnerability assessment scan Id of the scan to retrieve.|scan_id|scanId|

### synapse s-q-l-pool-vulnerability-assessment-scan list

list a synapse s-q-l-pool-vulnerability-assessment-scan.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse s-q-l-pool-vulnerability-assessment-scan|SqlPoolVulnerabilityAssessmentScans|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--s-q-l-pool-name**|string|SQL pool name|s_q_l_pool_name|sqlPoolName|

### synapse workspace create

create a synapse workspace.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace|Workspaces|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--location**|string|The geo-location where the resource lives|location|location|
|**--tags**|dictionary|Resource tags.|tags|tags|
|**--default-data-lake-storage**|object|Workspace default data lake storage account details|default_data_lake_storage|defaultDataLakeStorage|
|**--sql-administrator-login-password**|string|SQL administrator login password|s_q_l_administrator_login_password|sqlAdministratorLoginPassword|
|**--managed-resource-group-name**|string|Workspace managed resource group. The resource group name uniquely identifies the resource group within the user subscriptionId. The resource group name must be no longer than 90 characters long, and must be alphanumeric characters (Char.IsLetterOrDigit()) and '-', '_', '(', ')' and'.'. Note that the name cannot end with '.'|managed_resource_group_name|managedResourceGroupName|
|**--sql-administrator-login**|string|Login for workspace SQL active directory administrator|s_q_l_administrator_login|sqlAdministratorLogin|
|**--connectivity-endpoints**|dictionary|Connectivity endpoints|connectivity_endpoints|connectivityEndpoints|
|**--managed-virtual-network**|string|Setting this to 'default' will ensure that all compute for this workspace is in a virtual network managed on behalf of the user.|managed_virtual_network|managedVirtualNetwork|
|**--private-endpoint-connections**|array|Private endpoint connections to the workspace|private_endpoint_connections|privateEndpointConnections|
|**--virtual-network-profile-compute-subnet-id**|string|Subnet ID used for computes in workspace|compute_subnet_id|computeSubnetId|
|**--identity-type**|sealed-choice|The type of managed identity for the workspace|type|type|

### synapse workspace delete

delete a synapse workspace.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace|Workspaces|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

### synapse workspace list

list a synapse workspace.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace|Workspaces|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|list|ListByResourceGroup|
|list|List|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|

### synapse workspace show

show a synapse workspace.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace|Workspaces|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

### synapse workspace update

update a synapse workspace.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace|Workspaces|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--tags**|dictionary|Resource tags|tags|tags|
|**--sql-administrator-login-password**|string|SQL administrator login password|s_q_l_administrator_login_password|sqlAdministratorLoginPassword|
|**--identity-type**|sealed-choice|The type of managed identity for the workspace|type|type|

### synapse workspace-a-a-d-admin create

create a synapse workspace-a-a-d-admin.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace-a-a-d-admin|WorkspaceAadAdmins|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--tenant-id**|string|Tenant ID of the workspace active directory administrator|tenant_id|tenantId|
|**--login**|string|Login of the workspace active directory administrator|login|login|
|**--administrator-type**|string|Workspace active directory administrator type|administrator_type|administratorType|
|**--sid**|string|Object ID of the workspace active directory administrator|sid|sid|

### synapse workspace-a-a-d-admin delete

delete a synapse workspace-a-a-d-admin.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace-a-a-d-admin|WorkspaceAadAdmins|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|delete|Delete|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

### synapse workspace-a-a-d-admin show

show a synapse workspace-a-a-d-admin.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace-a-a-d-admin|WorkspaceAadAdmins|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

### synapse workspace-a-a-d-admin update

update a synapse workspace-a-a-d-admin.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace-a-a-d-admin|WorkspaceAadAdmins|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|CreateOrUpdate#Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--tenant-id**|string|Tenant ID of the workspace active directory administrator|tenant_id|tenantId|
|**--login**|string|Login of the workspace active directory administrator|login|login|
|**--administrator-type**|string|Workspace active directory administrator type|administrator_type|administratorType|
|**--sid**|string|Object ID of the workspace active directory administrator|sid|sid|

### synapse workspace-managed-identity-s-q-l-control-setting create

create a synapse workspace-managed-identity-s-q-l-control-setting.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace-managed-identity-s-q-l-control-setting|WorkspaceManagedIdentitySqlControlSettings|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|create|CreateOrUpdate#Create|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--grant-sql-control-to-managed-identity-desired-state**|choice|Desired state|desired_state|desiredState|

### synapse workspace-managed-identity-s-q-l-control-setting show

show a synapse workspace-managed-identity-s-q-l-control-setting.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace-managed-identity-s-q-l-control-setting|WorkspaceManagedIdentitySqlControlSettings|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|show|Get|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|

### synapse workspace-managed-identity-s-q-l-control-setting update

update a synapse workspace-managed-identity-s-q-l-control-setting.

#### Command group
|Name (az)|Swagger name|
|---------|------------|
|synapse workspace-managed-identity-s-q-l-control-setting|WorkspaceManagedIdentitySqlControlSettings|

#### Methods
|Name (az)|Swagger name|
|---------|------------|
|update|CreateOrUpdate#Update|

#### Parameters
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group. The name is case insensitive.|resource_group_name|resourceGroupName|
|**--workspace-name**|string|The name of the workspace|workspace_name|workspaceName|
|**--grant-sql-control-to-managed-identity-desired-state**|choice|Desired state|desired_state|desiredState|
