# Azure CLI Module Creation Report

## EXTENSION
|CLI Extension|Command Groups|
|---------|------------|
|az billing|[groups](#CommandGroups)

## GROUPS
### <a name="CommandGroups">Command groups in `az billing` extension </a>
|CLI Command Group|Group Swagger name|Commands|
|---------|------------|--------|
|az billing account|BillingAccounts|[commands](#CommandsInBillingAccounts)|
|az billing balance|AvailableBalances|[commands](#CommandsInAvailableBalances)|
|az billing profile|BillingProfiles|[commands](#CommandsInBillingProfiles)|
|az billing customer|Customers|[commands](#CommandsInCustomers)|
|az billing subscription|BillingSubscriptions|[commands](#CommandsInBillingSubscriptions)|
|az billing product|Products|[commands](#CommandsInProducts)|
|az billing transaction|Transactions|[commands](#CommandsInTransactions)|
|az billing policy|Policies|[commands](#CommandsInPolicies)|
|az billing property|BillingProperty|[commands](#CommandsInBillingProperty)|

## COMMANDS
### <a name="CommandsInBillingAccounts">Commands in `az billing account` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az billing account list](#BillingAccountsList)|List|[Parameters](#ParametersBillingAccountsList)|[Example](#ExamplesBillingAccountsList)|
|[az billing account show](#BillingAccountsGet)|Get|[Parameters](#ParametersBillingAccountsGet)|[Example](#ExamplesBillingAccountsGet)|
|[az billing account update](#BillingAccountsUpdate)|Update|[Parameters](#ParametersBillingAccountsUpdate)|[Example](#ExamplesBillingAccountsUpdate)|

### <a name="CommandsInAvailableBalances">Commands in `az billing balance` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az billing balance show](#AvailableBalancesGet)|Get|[Parameters](#ParametersAvailableBalancesGet)|[Example](#ExamplesAvailableBalancesGet)|

### <a name="CommandsInCustomers">Commands in `az billing customer` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az billing customer list](#CustomersListByBillingProfile)|ListByBillingProfile|[Parameters](#ParametersCustomersListByBillingProfile)|[Example](#ExamplesCustomersListByBillingProfile)|
|[az billing customer list](#CustomersListByBillingAccount)|ListByBillingAccount|[Parameters](#ParametersCustomersListByBillingAccount)|[Example](#ExamplesCustomersListByBillingAccount)|
|[az billing customer show](#CustomersGet)|Get|[Parameters](#ParametersCustomersGet)|[Example](#ExamplesCustomersGet)|

### <a name="CommandsInPolicies">Commands in `az billing policy` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az billing policy show](#PoliciesGetByCustomer)|GetByCustomer|[Parameters](#ParametersPoliciesGetByCustomer)|[Example](#ExamplesPoliciesGetByCustomer)|
|[az billing policy update](#PoliciesUpdate)|Update|[Parameters](#ParametersPoliciesUpdate)|[Example](#ExamplesPoliciesUpdate)|

### <a name="CommandsInProducts">Commands in `az billing product` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az billing product list](#ProductsListByInvoiceSection)|ListByInvoiceSection|[Parameters](#ParametersProductsListByInvoiceSection)|[Example](#ExamplesProductsListByInvoiceSection)|
|[az billing product list](#ProductsListByBillingProfile)|ListByBillingProfile|[Parameters](#ParametersProductsListByBillingProfile)|[Example](#ExamplesProductsListByBillingProfile)|
|[az billing product list](#ProductsListByCustomer)|ListByCustomer|[Parameters](#ParametersProductsListByCustomer)|[Example](#ExamplesProductsListByCustomer)|
|[az billing product list](#ProductsListByBillingAccount)|ListByBillingAccount|[Parameters](#ParametersProductsListByBillingAccount)|[Example](#ExamplesProductsListByBillingAccount)|
|[az billing product show](#ProductsGet)|Get|[Parameters](#ParametersProductsGet)|[Example](#ExamplesProductsGet)|
|[az billing product update](#ProductsUpdate)|Update|[Parameters](#ParametersProductsUpdate)|[Example](#ExamplesProductsUpdate)|
|[az billing product move](#ProductsMove)|Move|[Parameters](#ParametersProductsMove)|[Example](#ExamplesProductsMove)|
|[az billing product validate-move](#ProductsValidateMove)|ValidateMove|[Parameters](#ParametersProductsValidateMove)|[Example](#ExamplesProductsValidateMove)|

### <a name="CommandsInBillingProfiles">Commands in `az billing profile` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az billing profile list](#BillingProfilesListByBillingAccount)|ListByBillingAccount|[Parameters](#ParametersBillingProfilesListByBillingAccount)|[Example](#ExamplesBillingProfilesListByBillingAccount)|
|[az billing profile show](#BillingProfilesGet)|Get|[Parameters](#ParametersBillingProfilesGet)|[Example](#ExamplesBillingProfilesGet)|
|[az billing profile create](#BillingProfilesCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersBillingProfilesCreateOrUpdate#Create)|[Example](#ExamplesBillingProfilesCreateOrUpdate#Create)|
|[az billing profile update](#BillingProfilesCreateOrUpdate#Update)|CreateOrUpdate#Update|[Parameters](#ParametersBillingProfilesCreateOrUpdate#Update)|Not Found|

### <a name="CommandsInBillingProperty">Commands in `az billing property` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az billing property show](#BillingPropertyGet)|Get|[Parameters](#ParametersBillingPropertyGet)|[Example](#ExamplesBillingPropertyGet)|
|[az billing property update](#BillingPropertyUpdate)|Update|[Parameters](#ParametersBillingPropertyUpdate)|[Example](#ExamplesBillingPropertyUpdate)|

### <a name="CommandsInBillingSubscriptions">Commands in `az billing subscription` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az billing subscription list](#BillingSubscriptionsListByInvoiceSection)|ListByInvoiceSection|[Parameters](#ParametersBillingSubscriptionsListByInvoiceSection)|[Example](#ExamplesBillingSubscriptionsListByInvoiceSection)|
|[az billing subscription list](#BillingSubscriptionsListByCustomer)|ListByCustomer|[Parameters](#ParametersBillingSubscriptionsListByCustomer)|[Example](#ExamplesBillingSubscriptionsListByCustomer)|
|[az billing subscription list](#BillingSubscriptionsListByBillingProfile)|ListByBillingProfile|[Parameters](#ParametersBillingSubscriptionsListByBillingProfile)|[Example](#ExamplesBillingSubscriptionsListByBillingProfile)|
|[az billing subscription list](#BillingSubscriptionsListByBillingAccount)|ListByBillingAccount|[Parameters](#ParametersBillingSubscriptionsListByBillingAccount)|[Example](#ExamplesBillingSubscriptionsListByBillingAccount)|
|[az billing subscription show](#BillingSubscriptionsGet)|Get|[Parameters](#ParametersBillingSubscriptionsGet)|[Example](#ExamplesBillingSubscriptionsGet)|
|[az billing subscription update](#BillingSubscriptionsUpdate)|Update|[Parameters](#ParametersBillingSubscriptionsUpdate)|[Example](#ExamplesBillingSubscriptionsUpdate)|
|[az billing subscription move](#BillingSubscriptionsMove)|Move|[Parameters](#ParametersBillingSubscriptionsMove)|[Example](#ExamplesBillingSubscriptionsMove)|
|[az billing subscription validate-move](#BillingSubscriptionsValidateMove)|ValidateMove|[Parameters](#ParametersBillingSubscriptionsValidateMove)|[Example](#ExamplesBillingSubscriptionsValidateMove)|

### <a name="CommandsInTransactions">Commands in `az billing transaction` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az billing transaction list](#TransactionsListByInvoice)|ListByInvoice|[Parameters](#ParametersTransactionsListByInvoice)|[Example](#ExamplesTransactionsListByInvoice)|


## COMMAND DETAILS

### group `az billing account`
#### <a name="BillingAccountsList">Command `az billing account list`</a>

##### <a name="ExamplesBillingAccountsList">Example</a>
```
az billing account list
```
##### <a name="ExamplesBillingAccountsList">Example</a>
```
az billing account list --expand "soldTo,billingProfiles,billingProfiles/invoiceSections"
```
##### <a name="ExamplesBillingAccountsList">Example</a>
```
az billing account list --expand "enrollmentDetails,departments,enrollmentAccounts"
```
##### <a name="ParametersBillingAccountsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--expand**|string|May be used to expand the soldTo, invoice sections and billing profiles.|expand|$expand|

#### <a name="BillingAccountsGet">Command `az billing account show`</a>

##### <a name="ExamplesBillingAccountsGet">Example</a>
```
az billing account show --expand "soldTo,billingProfiles,billingProfiles/invoiceSections" --name \
"{billingAccountName}"
```
##### <a name="ExamplesBillingAccountsGet">Example</a>
```
az billing account show --name "{billingAccountName}"
```
##### <a name="ParametersBillingAccountsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--expand**|string|May be used to expand the soldTo, invoice sections and billing profiles.|expand|$expand|

#### <a name="BillingAccountsUpdate">Command `az billing account update`</a>

##### <a name="ExamplesBillingAccountsUpdate">Example</a>
```
az billing account update --name "{billingAccountName}" --display-name "Test Account" --sold-to address-line1="Test \
Address 1" city="Redmond" company-name="Contoso" country="US" first-name="Test" last-name="User" postal-code="12345" \
region="WA"
```
##### <a name="ParametersBillingAccountsUpdate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--display-name**|string|The billing account name.|display_name|displayName|
|**--sold-to**|object|The address of the individual or organization that is responsible for the billing account.|sold_to|soldTo|
|**--departments**|array|The departments associated to the enrollment.|departments|departments|
|**--enrollment-accounts**|array|The accounts associated to the enrollment.|enrollment_accounts|enrollmentAccounts|
|**--billing-profiles-value**|array|The billing profiles associated with the billing account.|value|value|

### group `az billing balance`
#### <a name="AvailableBalancesGet">Command `az billing balance show`</a>

##### <a name="ExamplesAvailableBalancesGet">Example</a>
```
az billing balance show --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
```
##### <a name="ParametersAvailableBalancesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--profile-name**|string|The ID that uniquely identifies a billing profile.|profile_name|billingProfileName|

### group `az billing customer`
#### <a name="CustomersListByBillingProfile">Command `az billing customer list`</a>

##### <a name="ExamplesCustomersListByBillingProfile">Example</a>
```
az billing customer list --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
```
##### <a name="ParametersCustomersListByBillingProfile">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--profile-name**|string|The ID that uniquely identifies a billing profile.|profile_name|billingProfileName|
|**--search**|string|Used for searching customers by their name. Any customer with name containing the search text will be included in the response|search|$search|
|**--filter**|string|May be used to filter the list of customers.|filter|$filter|

#### <a name="CustomersListByBillingAccount">Command `az billing customer list`</a>

##### <a name="ExamplesCustomersListByBillingAccount">Example</a>
```
az billing customer list --account-name "{billingAccountName}"
```
##### <a name="ParametersCustomersListByBillingAccount">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
#### <a name="CustomersGet">Command `az billing customer show`</a>

##### <a name="ExamplesCustomersGet">Example</a>
```
az billing customer show --account-name "{billingAccountName}" --name "{customerName}"
```
##### <a name="ExamplesCustomersGet">Example</a>
```
az billing customer show --expand "enabledAzurePlans,resellers" --account-name "{billingAccountName}" --name \
"{customerName}"
```
##### <a name="ParametersCustomersGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--customer-name**|string|The ID that uniquely identifies a customer.|customer_name|customerName|
|**--expand**|string|May be used to expand enabledAzurePlans and resellers|expand|$expand|

### group `az billing policy`
#### <a name="PoliciesGetByCustomer">Command `az billing policy show`</a>

##### <a name="ExamplesPoliciesGetByCustomer">Example</a>
```
az billing policy show --account-name "{billingAccountName}" --customer-name "{customerName}"
```
##### <a name="ParametersPoliciesGetByCustomer">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--customer-name**|string|The ID that uniquely identifies a customer.|customer_name|customerName|

#### <a name="PoliciesUpdate">Command `az billing policy update`</a>

##### <a name="ExamplesPoliciesUpdate">Example</a>
```
az billing policy update --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--marketplace-purchases "OnlyFreeAllowed" --reservation-purchases "NotAllowed" --view-charges "Allowed"
```
##### <a name="ParametersPoliciesUpdate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--profile-name**|string|The ID that uniquely identifies a billing profile.|profile_name|billingProfileName|
|**--marketplace-purchases**|choice|The policy that controls whether Azure marketplace purchases are allowed for a billing profile.|marketplace_purchases|marketplacePurchases|
|**--reservation-purchases**|choice|The policy that controls whether Azure reservation purchases are allowed for a billing profile.|reservation_purchases|reservationPurchases|
|**--view-charges**|choice|The policy that controls whether users with Azure RBAC access to a subscription can view its charges.|view_charges|viewCharges|

### group `az billing product`
#### <a name="ProductsListByInvoiceSection">Command `az billing product list`</a>

##### <a name="ExamplesProductsListByInvoiceSection">Example</a>
```
az billing product list --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--invoice-section-name "{invoiceSectionName}"
```
##### <a name="ParametersProductsListByInvoiceSection">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--profile-name**|string|The ID that uniquely identifies a billing profile.|profile_name|billingProfileName|
|**--invoice-section-name**|string|The ID that uniquely identifies an invoice section.|invoice_section_name|invoiceSectionName|
|**--filter**|string|May be used to filter by product type. The filter supports 'eq', 'lt', 'gt', 'le', 'ge', and 'and'. It does not currently support 'ne', 'or', or 'not'. Tag filter is a key value pair string where key and value are separated by a colon (:).|filter|$filter|

#### <a name="ProductsListByBillingProfile">Command `az billing product list`</a>

##### <a name="ExamplesProductsListByBillingProfile">Example</a>
```
az billing product list --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
```
##### <a name="ParametersProductsListByBillingProfile">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
#### <a name="ProductsListByCustomer">Command `az billing product list`</a>

##### <a name="ExamplesProductsListByCustomer">Example</a>
```
az billing product list --account-name "{billingAccountName}" --customer-name "{customerName}"
```
##### <a name="ParametersProductsListByCustomer">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--customer-name**|string|The ID that uniquely identifies a customer.|customer_name|customerName|

#### <a name="ProductsListByBillingAccount">Command `az billing product list`</a>

##### <a name="ExamplesProductsListByBillingAccount">Example</a>
```
az billing product list --account-name "{billingAccountName}"
```
##### <a name="ParametersProductsListByBillingAccount">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
#### <a name="ProductsGet">Command `az billing product show`</a>

##### <a name="ExamplesProductsGet">Example</a>
```
az billing product show --account-name "{billingAccountName}" --name "{productName}"
```
##### <a name="ParametersProductsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--product-name**|string|The ID that uniquely identifies a product.|product_name|productName|

#### <a name="ProductsUpdate">Command `az billing product update`</a>

##### <a name="ExamplesProductsUpdate">Example</a>
```
az billing product update --account-name "{billingAccountName}" --auto-renew "Off" --name "{productName}"
```
##### <a name="ParametersProductsUpdate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--product-name**|string|The ID that uniquely identifies a product.|product_name|productName|
|**--auto-renew**|choice|Indicates whether auto renewal is turned on or off for a product.|auto_renew|autoRenew|
|**--status**|choice|The current status of the product.|status|status|
|**--billing-frequency**|choice|The frequency at which the product will be billed.|billing_frequency|billingFrequency|

#### <a name="ProductsMove">Command `az billing product move`</a>

##### <a name="ExamplesProductsMove">Example</a>
```
az billing product move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}" --name "{productName}"
```
##### <a name="ParametersProductsMove">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--product-name**|string|The ID that uniquely identifies a product.|product_name|productName|
|**--destination-invoice-section-id**|string|The destination invoice section id.|destination_invoice_section_id|destinationInvoiceSectionId|

#### <a name="ProductsValidateMove">Command `az billing product validate-move`</a>

##### <a name="ExamplesProductsValidateMove">Example</a>
```
az billing product validate-move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}" --name "{productName}"
```
##### <a name="ExamplesProductsValidateMove">Example</a>
```
az billing product validate-move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}" --name "{productName}"
```
##### <a name="ParametersProductsValidateMove">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--product-name**|string|The ID that uniquely identifies a product.|product_name|productName|
|**--destination-invoice-section-id**|string|The destination invoice section id.|destination_invoice_section_id|destinationInvoiceSectionId|

### group `az billing profile`
#### <a name="BillingProfilesListByBillingAccount">Command `az billing profile list`</a>

##### <a name="ExamplesBillingProfilesListByBillingAccount">Example</a>
```
az billing profile list --account-name "{billingAccountName}"
```
##### <a name="ExamplesBillingProfilesListByBillingAccount">Example</a>
```
az billing profile list --expand "invoiceSections" --account-name "{billingAccountName}"
```
##### <a name="ParametersBillingProfilesListByBillingAccount">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--expand**|string|May be used to expand the invoice sections.|expand|$expand|

#### <a name="BillingProfilesGet">Command `az billing profile show`</a>

##### <a name="ExamplesBillingProfilesGet">Example</a>
```
az billing profile show --account-name "{billingAccountName}" --name "{billingProfileName}"
```
##### <a name="ExamplesBillingProfilesGet">Example</a>
```
az billing profile show --expand "invoiceSections" --account-name "{billingAccountName}" --name "{billingProfileName}"
```
##### <a name="ParametersBillingProfilesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--profile-name**|string|The ID that uniquely identifies a billing profile.|profile_name|billingProfileName|
|**--expand**|string|May be used to expand the invoice sections.|expand|$expand|

#### <a name="BillingProfilesCreateOrUpdate#Create">Command `az billing profile create`</a>

##### <a name="ExamplesBillingProfilesCreateOrUpdate#Create">Example</a>
```
az billing profile create --account-name "{billingAccountName}" --name "{billingProfileName}" --bill-to \
address-line1="Test Address 1" city="Redmond" country="US" first-name="Test" last-name="User" postal-code="12345" \
region="WA" --display-name "Finance" --enabled-azure-plans sku-id="0001" --enabled-azure-plans sku-id="0002" \
--invoice-email-opt-in true --po-number "ABC12345"
```
##### <a name="ParametersBillingProfilesCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--profile-name**|string|The ID that uniquely identifies a billing profile.|profile_name|billingProfileName|
|**--display-name**|string|The name of the billing profile.|display_name|displayName|
|**--po-number**|string|The purchase order name that will appear on the invoices generated for the billing profile.|po_number|poNumber|
|**--bill-to**|object|Billing address.|bill_to|billTo|
|**--invoice-email-opt-in**|boolean|Flag controlling whether the invoices for the billing profile are sent through email.|invoice_email_opt_in|invoiceEmailOptIn|
|**--enabled-azure-plans**|array|Information about the enabled azure plans.|enabled_azure_plans|enabledAzurePlans|
|**--invoice-sections-value**|array|The invoice sections associated to the billing profile.|value|value|

#### <a name="BillingProfilesCreateOrUpdate#Update">Command `az billing profile update`</a>

##### <a name="ParametersBillingProfilesCreateOrUpdate#Update">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--profile-name**|string|The ID that uniquely identifies a billing profile.|profile_name|billingProfileName|
|**--display-name**|string|The name of the billing profile.|display_name|displayName|
|**--po-number**|string|The purchase order name that will appear on the invoices generated for the billing profile.|po_number|poNumber|
|**--bill-to**|object|Billing address.|bill_to|billTo|
|**--invoice-email-opt-in**|boolean|Flag controlling whether the invoices for the billing profile are sent through email.|invoice_email_opt_in|invoiceEmailOptIn|
|**--enabled-azure-plans**|array|Information about the enabled azure plans.|enabled_azure_plans|enabledAzurePlans|
|**--invoice-sections-value**|array|The invoice sections associated to the billing profile.|value|value|

### group `az billing property`
#### <a name="BillingPropertyGet">Command `az billing property show`</a>

##### <a name="ExamplesBillingPropertyGet">Example</a>
```
az billing property show
```
##### <a name="ParametersBillingPropertyGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
#### <a name="BillingPropertyUpdate">Command `az billing property update`</a>

##### <a name="ExamplesBillingPropertyUpdate">Example</a>
```
az billing property update --cost-center "1010"
```
##### <a name="ParametersBillingPropertyUpdate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--cost-center**|string|The cost center applied to the subscription.|cost_center|costCenter|

### group `az billing subscription`
#### <a name="BillingSubscriptionsListByInvoiceSection">Command `az billing subscription list`</a>

##### <a name="ExamplesBillingSubscriptionsListByInvoiceSection">Example</a>
```
az billing subscription list --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--invoice-section-name "{invoiceSectionName}"
```
##### <a name="ParametersBillingSubscriptionsListByInvoiceSection">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--profile-name**|string|The ID that uniquely identifies a billing profile.|profile_name|billingProfileName|
|**--invoice-section-name**|string|The ID that uniquely identifies an invoice section.|invoice_section_name|invoiceSectionName|

#### <a name="BillingSubscriptionsListByCustomer">Command `az billing subscription list`</a>

##### <a name="ExamplesBillingSubscriptionsListByCustomer">Example</a>
```
az billing subscription list --account-name "{billingAccountName}" --customer-name "{customerName}"
```
##### <a name="ParametersBillingSubscriptionsListByCustomer">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--customer-name**|string|The ID that uniquely identifies a customer.|customer_name|customerName|

#### <a name="BillingSubscriptionsListByBillingProfile">Command `az billing subscription list`</a>

##### <a name="ExamplesBillingSubscriptionsListByBillingProfile">Example</a>
```
az billing subscription list --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
```
##### <a name="ParametersBillingSubscriptionsListByBillingProfile">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
#### <a name="BillingSubscriptionsListByBillingAccount">Command `az billing subscription list`</a>

##### <a name="ExamplesBillingSubscriptionsListByBillingAccount">Example</a>
```
az billing subscription list --account-name "{billingAccountName}"
```
##### <a name="ParametersBillingSubscriptionsListByBillingAccount">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
#### <a name="BillingSubscriptionsGet">Command `az billing subscription show`</a>

##### <a name="ExamplesBillingSubscriptionsGet">Example</a>
```
az billing subscription show --account-name "{billingAccountName}"
```
##### <a name="ParametersBillingSubscriptionsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|

#### <a name="BillingSubscriptionsUpdate">Command `az billing subscription update`</a>

##### <a name="ExamplesBillingSubscriptionsUpdate">Example</a>
```
az billing subscription update --account-name "{billingAccountName}" --cost-center "ABC1234"
```
##### <a name="ParametersBillingSubscriptionsUpdate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--subscription-billing-status**|choice|The current billing status of the subscription.|subscription_billing_status|subscriptionBillingStatus|
|**--cost-center**|string|The cost center applied to the subscription.|cost_center|costCenter|
|**--sku-id**|string|The sku ID of the Azure plan for the subscription.|sku_id|skuId|

#### <a name="BillingSubscriptionsMove">Command `az billing subscription move`</a>

##### <a name="ExamplesBillingSubscriptionsMove">Example</a>
```
az billing subscription move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}"
```
##### <a name="ParametersBillingSubscriptionsMove">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--destination-invoice-section-id**|string|The destination invoice section id.|destination_invoice_section_id|destinationInvoiceSectionId|

#### <a name="BillingSubscriptionsValidateMove">Command `az billing subscription validate-move`</a>

##### <a name="ExamplesBillingSubscriptionsValidateMove">Example</a>
```
az billing subscription validate-move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}"
```
##### <a name="ExamplesBillingSubscriptionsValidateMove">Example</a>
```
az billing subscription validate-move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}"
```
##### <a name="ParametersBillingSubscriptionsValidateMove">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--destination-invoice-section-id**|string|The destination invoice section id.|destination_invoice_section_id|destinationInvoiceSectionId|

### group `az billing transaction`
#### <a name="TransactionsListByInvoice">Command `az billing transaction list`</a>

##### <a name="ExamplesTransactionsListByInvoice">Example</a>
```
az billing transaction list --account-name "{billingAccountName}" --invoice-name "{invoiceName}"
```
##### <a name="ParametersTransactionsListByInvoice">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--account-name**|string|The ID that uniquely identifies a billing account.|account_name|billingAccountName|
|**--invoice-name**|string|The ID that uniquely identifies an invoice.|invoice_name|invoiceName|
