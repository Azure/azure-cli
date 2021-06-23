# Azure CLI Module Creation Report

## EXTENSION
|CLI Extension|Command Groups|
|---------|------------|
|az marketplaceordering|[groups](#CommandGroups)

## GROUPS
### <a name="CommandGroups">Command groups in `az marketplaceordering` extension </a>
|CLI Command Group|Group Swagger name|Commands|
|---------|------------|--------|
|az term|MarketplaceAgreements|[commands](#CommandsInMarketplaceAgreements)|

## COMMANDS
### <a name="CommandsInMarketplaceAgreements">Commands in `az term` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az term show](#MarketplaceAgreementsGet)|Get|[Parameters](#ParametersMarketplaceAgreementsGet)|[Example](#ExamplesMarketplaceAgreementsGet)|
|[az term accept](#MarketplaceAgreementsCreate)|Create|[Parameters](#ParametersMarketplaceAgreementsCreate)|[Example](#ExamplesMarketplaceAgreementsCreate)|


## COMMAND DETAILS

### group `az term`
#### <a name="MarketplaceAgreementsGet">Command `az term show`</a>

##### <a name="ExamplesMarketplaceAgreementsGet">Example</a>
```
az term show --offer "offid" --plan "planid" --publisher "pubid"
```
##### <a name="ParametersMarketplaceAgreementsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--publisher**|string|Publisher identifier string of image being deployed.|publisher|publisherId|
|**--offer**|string|Offer identifier string of image being deployed.|offer|offerId|
|**--plan**|string|Plan identifier string of image being deployed.|plan|planId|

#### <a name="MarketplaceAgreementsCreate">Command `az term accept`</a>

##### <a name="ExamplesMarketplaceAgreementsCreate">Example</a>
```
az term accept --offer "offid" --plan "planid" --offer "offid" --publisher "pubid" --plan "planid" --publisher "pubid"
```
##### <a name="ParametersMarketplaceAgreementsCreate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--publisher**|string|Publisher identifier string of image being deployed.|publisher|publisherId|
|**--offer**|string|Offer identifier string of image being deployed.|offer|offerId|
|**--plan**|string|Plan identifier string of image being deployed.|plan|planId|
|**--publisher**|string|Publisher identifier string of image being deployed.|publisher|publisher|
|**--offer**|string|Offer identifier string of image being deployed.|offer|product|
|**--plan**|string|Plan identifier string of image being deployed.|plan|plan|
