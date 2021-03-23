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
|[az term show](#MarketplaceAgreementsGetAgreement)|GetAgreement|[Parameters](#ParametersMarketplaceAgreementsGetAgreement)|[Example](#ExamplesMarketplaceAgreementsGetAgreement)|
|[az term cancel](#MarketplaceAgreementsCancel)|Cancel|[Parameters](#ParametersMarketplaceAgreementsCancel)|[Example](#ExamplesMarketplaceAgreementsCancel)|
|[az term sign](#MarketplaceAgreementsSign)|Sign|[Parameters](#ParametersMarketplaceAgreementsSign)|[Example](#ExamplesMarketplaceAgreementsSign)|


## COMMAND DETAILS

### group `az term`
#### <a name="MarketplaceAgreementsGetAgreement">Command `az term show`</a>

##### <a name="ExamplesMarketplaceAgreementsGetAgreement">Example</a>
```
az term show --offer "offid" --plan "planid" --publisher "pubid"
```
##### <a name="ParametersMarketplaceAgreementsGetAgreement">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--publisher**|string|Publisher identifier string of image being deployed.|publisher|publisherId|
|**--offer**|string|Offer identifier string of image being deployed.|offer|offerId|
|**--plan**|string|Plan identifier string of image being deployed.|plan|planId|

#### <a name="MarketplaceAgreementsCancel">Command `az term cancel`</a>

##### <a name="ExamplesMarketplaceAgreementsCancel">Example</a>
```
az term cancel --offer "offid" --plan "planid" --publisher "pubid"
```
##### <a name="ParametersMarketplaceAgreementsCancel">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--publisher**|string|Publisher identifier string of image being deployed.|publisher|publisherId|
|**--offer**|string|Offer identifier string of image being deployed.|offer|offerId|
|**--plan**|string|Plan identifier string of image being deployed.|plan|planId|

#### <a name="MarketplaceAgreementsSign">Command `az term sign`</a>

##### <a name="ExamplesMarketplaceAgreementsSign">Example</a>
```
az term sign --offer "offid" --plan "planid" --publisher "pubid"
```
##### <a name="ParametersMarketplaceAgreementsSign">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--publisher**|string|Publisher identifier string of image being deployed.|publisher|publisherId|
|**--offer**|string|Offer identifier string of image being deployed.|offer|offerId|
|**--plan**|string|Plan identifier string of image being deployed.|plan|planId|
