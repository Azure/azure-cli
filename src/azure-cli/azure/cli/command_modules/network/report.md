# Azure CLI Module Creation Report

## EXTENSION
|CLI Extension|Command Groups|
|---------|------------|
|az network|[groups](#CommandGroups)

## GROUPS
### <a name="CommandGroups">Command groups in `az network` extension </a>
|CLI Command Group|Group Swagger name|Commands|
|---------|------------|--------|
|az network express-route peering connection|ExpressRouteCircuitConnections|[commands](#CommandsInExpressRouteCircuitConnections)|
|az network express-route|ExpressRouteCircuits|[commands](#CommandsInExpressRouteCircuits)|

## COMMANDS
### <a name="CommandsInExpressRouteCircuits">Commands in `az network express-route` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network express-route list-route-table-summary](#ExpressRouteCircuitsListRoutesTableSummary)|ListRoutesTableSummary|[Parameters](#ParametersExpressRouteCircuitsListRoutesTableSummary)|[Example](#ExamplesExpressRouteCircuitsListRoutesTableSummary)|
|[az network express-route show-peering-stat](#ExpressRouteCircuitsGetPeeringStats)|GetPeeringStats|[Parameters](#ParametersExpressRouteCircuitsGetPeeringStats)|[Example](#ExamplesExpressRouteCircuitsGetPeeringStats)|

### <a name="CommandsInExpressRouteCircuitConnections">Commands in `az network express-route peering connection` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az network express-route peering connection list](#ExpressRouteCircuitConnectionsList)|List|[Parameters](#ParametersExpressRouteCircuitConnectionsList)|[Example](#ExamplesExpressRouteCircuitConnectionsList)|


## COMMAND DETAILS

### group `az network express-route`
#### <a name="ExpressRouteCircuitsListRoutesTableSummary">Command `az network express-route list-route-table-summary`</a>

##### <a name="ExamplesExpressRouteCircuitsListRoutesTableSummary">Example</a>
```
az network express-route list-route-table-summary --circuit-name "circuitName" --device-path "devicePath" \
--peering-name "peeringName" --resource-group "rg1"
```
##### <a name="ParametersExpressRouteCircuitsListRoutesTableSummary">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--circuit-name**|string|The name of the express route circuit.|circuit_name|circuitName|
|**--peering-name**|string|The name of the peering.|peering_name|peeringName|
|**--device-path**|string|The path of the device.|device_path|devicePath|

#### <a name="ExpressRouteCircuitsGetPeeringStats">Command `az network express-route show-peering-stat`</a>

##### <a name="ExamplesExpressRouteCircuitsGetPeeringStats">Example</a>
```
az network express-route show-peering-stat --circuit-name "circuitName" --peering-name "peeringName" --resource-group \
"rg1"
```
##### <a name="ParametersExpressRouteCircuitsGetPeeringStats">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--circuit-name**|string|The name of the express route circuit.|circuit_name|circuitName|
|**--peering-name**|string|The name of the peering.|peering_name|peeringName|

### group `az network express-route peering connection`
#### <a name="ExpressRouteCircuitConnectionsList">Command `az network express-route peering connection list`</a>

##### <a name="ExamplesExpressRouteCircuitConnectionsList">Example</a>
```
az network express-route peering connection list --circuit-name "ExpressRouteARMCircuitA" --peering-name \
"AzurePrivatePeering" --resource-group "rg1"
```
##### <a name="ParametersExpressRouteCircuitConnectionsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--circuit-name**|string|The name of the circuit.|circuit_name|circuitName|
|**--peering-name**|string|The name of the peering.|peering_name|peeringName|
