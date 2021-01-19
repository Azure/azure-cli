# Azure CLI Module Creation Report

## EXTENSION
|CLI Extension|Command Groups|
|---------|------------|
|az databoxedge|[groups](#CommandGroups)

## GROUPS
### <a name="CommandGroups">Command groups in `az databoxedge` extension </a>
|CLI Command Group|Group Swagger name|Commands|
|---------|------------|--------|
|az databoxedge device|Devices|[commands](#CommandsInDevices)|
|az databoxedge alert|Alerts|[commands](#CommandsInAlerts)|
|az databoxedge bandwidth-schedule|BandwidthSchedules|[commands](#CommandsInBandwidthSchedules)|
|az databoxedge|Jobs|[commands](#CommandsInJobs)|
|az databoxedge|Nodes|[commands](#CommandsInNodes)|
|az databoxedge order|Orders|[commands](#CommandsInOrders)|
|az databoxedge|Skus|[commands](#CommandsInSkus)|

## COMMANDS
### <a name="CommandsInJobs">Commands in `az databoxedge` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az databoxedge show-job](#JobsGet)|Get|[Parameters](#ParametersJobsGet)|[Example](#ExamplesJobsGet)|

### <a name="CommandsInNodes">Commands in `az databoxedge` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az databoxedge list-node](#NodesListByDataBoxEdgeDevice)|ListByDataBoxEdgeDevice|[Parameters](#ParametersNodesListByDataBoxEdgeDevice)|[Example](#ExamplesNodesListByDataBoxEdgeDevice)|

### <a name="CommandsInSkus">Commands in `az databoxedge` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az databoxedge list-sku](#SkusList)|List|[Parameters](#ParametersSkusList)|[Example](#ExamplesSkusList)|

### <a name="CommandsInAlerts">Commands in `az databoxedge alert` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az databoxedge alert list](#AlertsListByDataBoxEdgeDevice)|ListByDataBoxEdgeDevice|[Parameters](#ParametersAlertsListByDataBoxEdgeDevice)|[Example](#ExamplesAlertsListByDataBoxEdgeDevice)|
|[az databoxedge alert show](#AlertsGet)|Get|[Parameters](#ParametersAlertsGet)|[Example](#ExamplesAlertsGet)|

### <a name="CommandsInBandwidthSchedules">Commands in `az databoxedge bandwidth-schedule` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az databoxedge bandwidth-schedule list](#BandwidthSchedulesListByDataBoxEdgeDevice)|ListByDataBoxEdgeDevice|[Parameters](#ParametersBandwidthSchedulesListByDataBoxEdgeDevice)|[Example](#ExamplesBandwidthSchedulesListByDataBoxEdgeDevice)|
|[az databoxedge bandwidth-schedule show](#BandwidthSchedulesGet)|Get|[Parameters](#ParametersBandwidthSchedulesGet)|[Example](#ExamplesBandwidthSchedulesGet)|
|[az databoxedge bandwidth-schedule create](#BandwidthSchedulesCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersBandwidthSchedulesCreateOrUpdate#Create)|[Example](#ExamplesBandwidthSchedulesCreateOrUpdate#Create)|
|[az databoxedge bandwidth-schedule update](#BandwidthSchedulesCreateOrUpdate#Update)|CreateOrUpdate#Update|[Parameters](#ParametersBandwidthSchedulesCreateOrUpdate#Update)|Not Found|
|[az databoxedge bandwidth-schedule delete](#BandwidthSchedulesDelete)|Delete|[Parameters](#ParametersBandwidthSchedulesDelete)|[Example](#ExamplesBandwidthSchedulesDelete)|

### <a name="CommandsInDevices">Commands in `az databoxedge device` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az databoxedge device list](#DevicesListByResourceGroup)|ListByResourceGroup|[Parameters](#ParametersDevicesListByResourceGroup)|[Example](#ExamplesDevicesListByResourceGroup)|
|[az databoxedge device list](#DevicesListBySubscription)|ListBySubscription|[Parameters](#ParametersDevicesListBySubscription)|[Example](#ExamplesDevicesListBySubscription)|
|[az databoxedge device show](#DevicesGet)|Get|[Parameters](#ParametersDevicesGet)|[Example](#ExamplesDevicesGet)|
|[az databoxedge device create](#DevicesCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersDevicesCreateOrUpdate#Create)|[Example](#ExamplesDevicesCreateOrUpdate#Create)|
|[az databoxedge device update](#DevicesUpdate)|Update|[Parameters](#ParametersDevicesUpdate)|[Example](#ExamplesDevicesUpdate)|
|[az databoxedge device delete](#DevicesDelete)|Delete|[Parameters](#ParametersDevicesDelete)|[Example](#ExamplesDevicesDelete)|
|[az databoxedge device download-update](#DevicesDownloadUpdates)|DownloadUpdates|[Parameters](#ParametersDevicesDownloadUpdates)|[Example](#ExamplesDevicesDownloadUpdates)|
|[az databoxedge device install-update](#DevicesInstallUpdates)|InstallUpdates|[Parameters](#ParametersDevicesInstallUpdates)|[Example](#ExamplesDevicesInstallUpdates)|
|[az databoxedge device scan-for-update](#DevicesScanForUpdates)|ScanForUpdates|[Parameters](#ParametersDevicesScanForUpdates)|[Example](#ExamplesDevicesScanForUpdates)|
|[az databoxedge device show-update-summary](#DevicesGetUpdateSummary)|GetUpdateSummary|[Parameters](#ParametersDevicesGetUpdateSummary)|[Example](#ExamplesDevicesGetUpdateSummary)|

### <a name="CommandsInOrders">Commands in `az databoxedge order` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az databoxedge order list](#OrdersListByDataBoxEdgeDevice)|ListByDataBoxEdgeDevice|[Parameters](#ParametersOrdersListByDataBoxEdgeDevice)|[Example](#ExamplesOrdersListByDataBoxEdgeDevice)|
|[az databoxedge order show](#OrdersGet)|Get|[Parameters](#ParametersOrdersGet)|[Example](#ExamplesOrdersGet)|
|[az databoxedge order create](#OrdersCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersOrdersCreateOrUpdate#Create)|[Example](#ExamplesOrdersCreateOrUpdate#Create)|
|[az databoxedge order update](#OrdersCreateOrUpdate#Update)|CreateOrUpdate#Update|[Parameters](#ParametersOrdersCreateOrUpdate#Update)|Not Found|
|[az databoxedge order delete](#OrdersDelete)|Delete|[Parameters](#ParametersOrdersDelete)|[Example](#ExamplesOrdersDelete)|


## COMMAND DETAILS

### group `az databoxedge`
#### <a name="JobsGet">Command `az databoxedge show-job`</a>

##### <a name="ExamplesJobsGet">Example</a>
```
az databoxedge show-job --name "159a00c7-8543-4343-9435-263ac87df3bb" --device-name "testedgedevice" --resource-group \
"GroupForEdgeAutomation"
```
##### <a name="ParametersJobsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--name**|string|The job name.|name|name|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

### group `az databoxedge`
#### <a name="NodesListByDataBoxEdgeDevice">Command `az databoxedge list-node`</a>

##### <a name="ExamplesNodesListByDataBoxEdgeDevice">Example</a>
```
az databoxedge list-node --device-name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersNodesListByDataBoxEdgeDevice">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

### group `az databoxedge`
#### <a name="SkusList">Command `az databoxedge list-sku`</a>

##### <a name="ExamplesSkusList">Example</a>
```
az databoxedge list-sku
```
##### <a name="ParametersSkusList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--filter**|string|Specify $filter='location eq <location>' to filter on location.|filter|$filter|

### group `az databoxedge alert`
#### <a name="AlertsListByDataBoxEdgeDevice">Command `az databoxedge alert list`</a>

##### <a name="ExamplesAlertsListByDataBoxEdgeDevice">Example</a>
```
az databoxedge alert list --device-name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersAlertsListByDataBoxEdgeDevice">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

#### <a name="AlertsGet">Command `az databoxedge alert show`</a>

##### <a name="ExamplesAlertsGet">Example</a>
```
az databoxedge alert show --name "159a00c7-8543-4343-9435-263ac87df3bb" --device-name "testedgedevice" \
--resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersAlertsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--name**|string|The alert name.|name|name|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

### group `az databoxedge bandwidth-schedule`
#### <a name="BandwidthSchedulesListByDataBoxEdgeDevice">Command `az databoxedge bandwidth-schedule list`</a>

##### <a name="ExamplesBandwidthSchedulesListByDataBoxEdgeDevice">Example</a>
```
az databoxedge bandwidth-schedule list --device-name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersBandwidthSchedulesListByDataBoxEdgeDevice">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

#### <a name="BandwidthSchedulesGet">Command `az databoxedge bandwidth-schedule show`</a>

##### <a name="ExamplesBandwidthSchedulesGet">Example</a>
```
az databoxedge bandwidth-schedule show --name "bandwidth-1" --device-name "testedgedevice" --resource-group \
"GroupForEdgeAutomation"
```
##### <a name="ParametersBandwidthSchedulesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--name**|string|The bandwidth schedule name.|name|name|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

#### <a name="BandwidthSchedulesCreateOrUpdate#Create">Command `az databoxedge bandwidth-schedule create`</a>

##### <a name="ExamplesBandwidthSchedulesCreateOrUpdate#Create">Example</a>
```
az databoxedge bandwidth-schedule create --name "bandwidth-1" --device-name "testedgedevice" --days "Sunday" "Monday" \
--rate-in-mbps 100 --start "0:0:0" --stop "13:59:0" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersBandwidthSchedulesCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--name**|string|The bandwidth schedule name which needs to be added/updated.|name|name|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|
|**--start**|string|The start time of the schedule in UTC.|start|start|
|**--stop**|string|The stop time of the schedule in UTC.|stop|stop|
|**--rate-in-mbps**|integer|The bandwidth rate in Mbps.|rate_in_mbps|rateInMbps|
|**--days**|array|The days of the week when this schedule is applicable.|days|days|

#### <a name="BandwidthSchedulesCreateOrUpdate#Update">Command `az databoxedge bandwidth-schedule update`</a>

##### <a name="ParametersBandwidthSchedulesCreateOrUpdate#Update">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--name**|string|The bandwidth schedule name which needs to be added/updated.|name|name|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|
|**--start**|string|The start time of the schedule in UTC.|start|start|
|**--stop**|string|The stop time of the schedule in UTC.|stop|stop|
|**--rate-in-mbps**|integer|The bandwidth rate in Mbps.|rate_in_mbps|rateInMbps|
|**--days**|array|The days of the week when this schedule is applicable.|days|days|

#### <a name="BandwidthSchedulesDelete">Command `az databoxedge bandwidth-schedule delete`</a>

##### <a name="ExamplesBandwidthSchedulesDelete">Example</a>
```
az databoxedge bandwidth-schedule delete --name "bandwidth-1" --device-name "testedgedevice" --resource-group \
"GroupForEdgeAutomation"
```
##### <a name="ParametersBandwidthSchedulesDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--name**|string|The bandwidth schedule name.|name|name|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

### group `az databoxedge device`
#### <a name="DevicesListByResourceGroup">Command `az databoxedge device list`</a>

##### <a name="ExamplesDevicesListByResourceGroup">Example</a>
```
az databoxedge device list --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersDevicesListByResourceGroup">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|
|**--expand**|string|Specify $expand=details to populate additional fields related to the resource or Specify $skipToken=<token> to populate the next page in the list.|expand|$expand|

#### <a name="DevicesListBySubscription">Command `az databoxedge device list`</a>

##### <a name="ExamplesDevicesListBySubscription">Example</a>
```
az databoxedge device list
```
##### <a name="ParametersDevicesListBySubscription">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
#### <a name="DevicesGet">Command `az databoxedge device show`</a>

##### <a name="ExamplesDevicesGet">Example</a>
```
az databoxedge device show --name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersDevicesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

#### <a name="DevicesCreateOrUpdate#Create">Command `az databoxedge device create`</a>

##### <a name="ExamplesDevicesCreateOrUpdate#Create">Example</a>
```
az databoxedge device create --location "eastus" --sku name="Edge" tier="Standard" --name "testedgedevice" \
--resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersDevicesCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|
|**--location**|string|The location of the device. This is a supported and registered Azure geographical region (for example, West US, East US, or Southeast Asia). The geographical region of a device cannot be changed once it is created, but if an identical geographical region is specified on update, the request will succeed.|location|location|
|**--tags**|dictionary|The list of tags that describe the device. These tags can be used to view and group this device (across resource groups).|tags|tags|
|**--sku**|object|The SKU type.|sku|sku|
|**--etag**|string|The etag for the devices.|etag|etag|
|**--data-box-edge-device-status**|choice|The status of the Data Box Edge/Gateway device.|data_box_edge_device_status|dataBoxEdgeDeviceStatus|
|**--description**|string|The Description of the Data Box Edge/Gateway device.|description|description|
|**--model-description**|string|The description of the Data Box Edge/Gateway device model.|model_description|modelDescription|
|**--friendly-name**|string|The Data Box Edge/Gateway device name.|friendly_name|friendlyName|

#### <a name="DevicesUpdate">Command `az databoxedge device update`</a>

##### <a name="ExamplesDevicesUpdate">Example</a>
```
az databoxedge device update --name "testedgedevice" --tags Key1="value1" Key2="value2" --resource-group \
"GroupForEdgeAutomation"
```
##### <a name="ParametersDevicesUpdate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|
|**--tags**|dictionary|The tags attached to the Data Box Edge/Gateway resource.|tags|tags|

#### <a name="DevicesDelete">Command `az databoxedge device delete`</a>

##### <a name="ExamplesDevicesDelete">Example</a>
```
az databoxedge device delete --name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersDevicesDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

#### <a name="DevicesDownloadUpdates">Command `az databoxedge device download-update`</a>

##### <a name="ExamplesDevicesDownloadUpdates">Example</a>
```
az databoxedge device download-update --name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersDevicesDownloadUpdates">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

#### <a name="DevicesInstallUpdates">Command `az databoxedge device install-update`</a>

##### <a name="ExamplesDevicesInstallUpdates">Example</a>
```
az databoxedge device install-update --name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersDevicesInstallUpdates">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

#### <a name="DevicesScanForUpdates">Command `az databoxedge device scan-for-update`</a>

##### <a name="ExamplesDevicesScanForUpdates">Example</a>
```
az databoxedge device scan-for-update --name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersDevicesScanForUpdates">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

#### <a name="DevicesGetUpdateSummary">Command `az databoxedge device show-update-summary`</a>

##### <a name="ExamplesDevicesGetUpdateSummary">Example</a>
```
az databoxedge device show-update-summary --name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersDevicesGetUpdateSummary">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

### group `az databoxedge order`
#### <a name="OrdersListByDataBoxEdgeDevice">Command `az databoxedge order list`</a>

##### <a name="ExamplesOrdersListByDataBoxEdgeDevice">Example</a>
```
az databoxedge order list --device-name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersOrdersListByDataBoxEdgeDevice">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

#### <a name="OrdersGet">Command `az databoxedge order show`</a>

##### <a name="ExamplesOrdersGet">Example</a>
```
az databoxedge order show --device-name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersOrdersGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|

#### <a name="OrdersCreateOrUpdate#Create">Command `az databoxedge order create`</a>

##### <a name="ExamplesOrdersCreateOrUpdate#Create">Example</a>
```
az databoxedge order create --device-name "testedgedevice" --company-name "Microsoft" --contact-person "John Mcclane" \
--email-list "john@microsoft.com" --phone "(800) 426-9400" --address-line1 "Microsoft Corporation" --address-line2 \
"One Microsoft Way" --address-line3 "Redmond" --city "WA" --country "United States" --postal-code "98052" --state "WA" \
--resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersOrdersCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The order details of a device.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|
|**--status**|choice|Status of the order as per the allowed status types.|status|status|
|**--comments**|string|Comments related to this status change.|comments|comments|
|**--address-line1**|string|The address line1.|address_line1|addressLine1|
|**--address-line2**|string|The address line2.|address_line2|addressLine2|
|**--address-line3**|string|The address line3.|address_line3|addressLine3|
|**--postal-code**|string|The postal code.|postal_code|postalCode|
|**--city**|string|The city name.|city|city|
|**--state**|string|The state name.|state|state|
|**--country**|string|The country name.|country|country|
|**--contact-person**|string|The contact person name.|contact_person|contactPerson|
|**--company-name**|string|The name of the company.|company_name|companyName|
|**--phone**|string|The phone number.|phone|phone|
|**--email-list**|array|The email list.|email_list|emailList|

#### <a name="OrdersCreateOrUpdate#Update">Command `az databoxedge order update`</a>

##### <a name="ParametersOrdersCreateOrUpdate#Update">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The order details of a device.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|
|**--status**|choice|Status of the order as per the allowed status types.|status|status|
|**--comments**|string|Comments related to this status change.|comments|comments|
|**--address-line1**|string|The address line1.|address_line1|addressLine1|
|**--address-line2**|string|The address line2.|address_line2|addressLine2|
|**--address-line3**|string|The address line3.|address_line3|addressLine3|
|**--postal-code**|string|The postal code.|postal_code|postalCode|
|**--city**|string|The city name.|city|city|
|**--state**|string|The state name.|state|state|
|**--country**|string|The country name.|country|country|
|**--contact-person**|string|The contact person name.|contact_person|contactPerson|
|**--company-name**|string|The name of the company.|company_name|companyName|
|**--phone**|string|The phone number.|phone|phone|
|**--email-list**|array|The email list.|email_list|emailList|

#### <a name="OrdersDelete">Command `az databoxedge order delete`</a>

##### <a name="ExamplesOrdersDelete">Example</a>
```
az databoxedge order delete --device-name "testedgedevice" --resource-group "GroupForEdgeAutomation"
```
##### <a name="ParametersOrdersDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--device-name**|string|The device name.|device_name|deviceName|
|**--resource-group-name**|string|The resource group name.|resource_group_name|resourceGroupName|
