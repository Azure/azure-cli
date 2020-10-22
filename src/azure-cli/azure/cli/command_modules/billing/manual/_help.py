# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

from knack.help_files import helps


helps['billing account'] = """
    type: group
    short-summary: billing account
"""

helps['billing account list'] = """
    type: command
    short-summary: "Lists the billing accounts that a user has access to."
    examples:
      - name: List billing accounts
        text: |-
               az billing account list
      - name: List billing account with desired expanded arguments
        text: |-
               az billing account list --expand "soldTo,billingProfiles,billingProfiles/invoiceSections"
      - name: List billing account with desired expanded arguments
        text: |-
               az billing account list --expand "enrollmentDetails,departments,enrollmentAccounts"
"""

helps['billing account show'] = """
    type: command
    short-summary: "Gets a billing account by its ID."
    examples:
      - name: Show an billing acount with expanded properties
        text: |-
               az billing account show --expand "soldTo,billingProfiles,billingProfiles/invoiceSections" --name \
"{billingAccountName}"
      - name: Show an billing acount with default properties
        text: |-
               az billing account show --name "{billingAccountName}"
"""

helps['billing account update'] = """
    type: command
    short-summary: "Updates the properties of a billing account. Currently, displayName and address can be updated. \
The operation is supported only for billing accounts with agreement type Microsoft Customer Agreement."
    parameters:
      - name: --sold-to
        short-summary: "The address of the individual or organization that is responsible for the billing account."
        long-summary: |
            Usage: --sold-to first-name=XX last-name=XX company-name=XX address-line1=XX address-line2=XX \
address-line3=XX city=XX district=XX region=XX country=XX postal-code=XX email=XX phone-number=XX
    examples:
      - name: UpdateBillingAccount
        text: |-
               az billing account update --name "{billingAccountName}" --display-name "Test Account" --sold-to \
address-line1="Test Address 1" city="Redmond" company-name="Contoso" country="US" first-name="Test" last-name="User" \
postal-code="12345" region="WA"
"""

helps['billing account wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the billing account is met.
    examples:
      - name: Pause executing next line of CLI script until the billing account is successfully updated.
        text: |-
               az billing account wait --name "{billingAccountName}" --updated
"""

helps['billing balance'] = """
    type: group
    short-summary: billing balance
"""

helps['billing balance show'] = """
    type: command
    short-summary: "The available credit balance for a billing profile. This is the balance that can be used for pay \
now to settle due or past due invoices. The operation is supported only for billing accounts with agreement type \
Microsoft Customer Agreement."
    examples:
      - name: AvailableBalanceByBillingProfile
        text: |-
               az billing balance show --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
"""

helps['billing profile'] = """
    type: group
    short-summary: Manage billing profile of billing account
"""

helps['billing profile list'] = """
    type: command
    short-summary: "List the billing profiles that a user has access to. The operation is supported for billing \
accounts with agreement type Microsoft Customer Agreement or Microsoft Partner Agreement."
    examples:
      - name: List billing profiles with default properties
        text: |-
               az billing profile list --account-name "{billingAccountName}"
      - name: List billing profiles with desired expanded properties
        text: |-
               az billing profile list --expand "invoiceSections" --account-name "{billingAccountName}"
"""

helps['billing profile show'] = """
    type: command
    short-summary: "Get a billing profile by its ID. The operation is supported for billing accounts with agreement \
type Microsoft Customer Agreement or Microsoft Partner Agreement."
    examples:
      - name: Show a billing profile with default properties
        text: |-
               az billing profile show --account-name "{billingAccountName}" --name "{billingProfileName}"
      - name: Show a billing profile with expaned properties
        text: |-
               az billing profile show --expand "invoiceSections" --account-name "{billingAccountName}" --name \
"{billingProfileName}"
"""

helps['billing profile create'] = """
    type: command
    short-summary: "Creates or updates a billing profile. The operation is supported for billing accounts with \
agreement type Microsoft Customer Agreement or Microsoft Partner Agreement."
    parameters:
      - name: --bill-to
        short-summary: "Billing address."
        long-summary: |
            Usage: --bill-to first-name=XX last-name=XX company-name=XX address-line1=XX address-line2=XX \
address-line3=XX city=XX district=XX region=XX country=XX postal-code=XX email=XX phone-number=XX
      - name: --enabled-azure-plans
        short-summary: "Information about the enabled azure plans."
        long-summary: |
            Usage: --enabled-azure-plans sku-id=XX
            sku-id: The sku id.
            Multiple actions can be specified by using more than one --enabled-azure-plans argument.
    examples:
      - name: Create a billing profile
        text: |-
               az billing profile create --account-name "{billingAccountName}" --name "{billingProfileName}" --bill-to \
address-line1="Test Address 1" city="Redmond" country="US" first-name="Test" last-name="User" postal-code="12345" \
region="WA" --display-name "Finance" --enabled-azure-plans sku-id="0001" --enabled-azure-plans sku-id="0002" \
--invoice-email-opt-in true --po-number "ABC12345"
"""

helps['billing profile update'] = """
    type: command
    short-summary: "Creates or updates a billing profile. The operation is supported for billing accounts with \
agreement type Microsoft Customer Agreement or Microsoft Partner Agreement."
    parameters:
      - name: --bill-to
        short-summary: "Billing address."
        long-summary: |
            Usage: --bill-to first-name=XX last-name=XX company-name=XX address-line1=XX address-line2=XX \
address-line3=XX city=XX district=XX region=XX country=XX postal-code=XX email=XX phone-number=XX
      - name: --enabled-azure-plans
        short-summary: "Information about the enabled azure plans."
        long-summary: |
            Usage: --enabled-azure-plans sku-id=XX
            sku-id: The sku id.
            Multiple actions can be specified by using more than one --enabled-azure-plans argument.
"""

helps['billing profile wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the billing profile is met.
    examples:
      - name: Pause executing next line of CLI script until the billing profile is successfully created.
        text: |-
               az billing profile wait --expand "invoiceSections" --account-name "{billingAccountName}" --name \
"{billingProfileName}" --created
      - name: Pause executing next line of CLI script until the billing profile is successfully updated.
        text: |-
               az billing profile wait --expand "invoiceSections" --account-name "{billingAccountName}" --name \
"{billingProfileName}" --updated
"""

helps['billing customer'] = """
    type: group
    short-summary: billing customer
"""

helps['billing customer list'] = """
    type: command
    short-summary: "Lists the customers that are billed to a billing account. The operation is supported only for \
billing accounts with agreement type Microsoft Partner Agreement."
    examples:
      - name: CustomersListByBillingAccount
        text: |-
               az billing customer list --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
"""

helps['billing customer show'] = """
    type: command
    short-summary: "Gets a customer by its ID. The operation is supported only for billing accounts with agreement \
type Microsoft Partner Agreement."
    examples:
      - name: Customer
        text: |-
               az billing customer show --account-name "{billingAccountName}" --name "{customerName}"
      - name: CustomerWithExpand
        text: |-
               az billing customer show --expand "enabledAzurePlans,resellers" --account-name "{billingAccountName}" \
--name "{customerName}"
"""

helps['billing invoice section'] = """
    type: group
    short-summary: billing invoice section
"""

helps['billing invoice section list'] = """
    type: command
    short-summary: "Lists the invoice sections that a user has access to. The operation is supported only for billing \
accounts with agreement type Microsoft Customer Agreement."
    examples:
      - name: InvoiceSectionsListByBillingProfile
        text: |-
               az billing invoice section list --account-name "{billingAccountName}" --profile-name \
"{billingProfileName}"
"""

helps['billing invoice section show'] = """
    type: command
    short-summary: "Gets an invoice section by its ID. The operation is supported only for billing accounts with \
agreement type Microsoft Customer Agreement."
    examples:
      - name: InvoiceSection
        text: |-
               az billing invoice section show --account-name "{billingAccountName}" --profile-name \
"{billingProfileName}" --name "{invoiceSectionName}"
"""

helps['billing invoice section create'] = """
    type: command
    short-summary: "Creates or updates an invoice section. The operation is supported only for billing accounts with \
agreement type Microsoft Customer Agreement."
    examples:
      - name: PutInvoiceSection
        text: |-
               az billing invoice section create --account-name "{billingAccountName}" --profile-name \
"{billingProfileName}" --name "{invoiceSectionName}" --display-name "invoiceSection1" --labels costCategory="Support" \
pcCode="A123456"
"""

helps['billing invoice section update'] = """
    type: command
    short-summary: "Creates or updates an invoice section. The operation is supported only for billing accounts with \
agreement type Microsoft Customer Agreement."
"""

helps['billing invoice section wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the billing invoice section is met.
    examples:
      - name: Pause executing next line of CLI script until the billing invoice section is successfully created.
        text: |-
               az billing invoice section wait --account-name "{billingAccountName}" --profile-name \
"{billingProfileName}" --name "{invoiceSectionName}" --created
      - name: Pause executing next line of CLI script until the billing invoice section is successfully updated.
        text: |-
               az billing invoice section wait --account-name "{billingAccountName}" --profile-name \
"{billingProfileName}" --name "{invoiceSectionName}" --updated
"""

helps['billing subscription'] = """
    type: group
    short-summary: billing subscription
"""

helps['billing subscription list'] = """
    type: command
    short-summary: "Lists the subscriptions for a billing account. The operation is supported for billing accounts \
with agreement type Microsoft Customer Agreement or Microsoft Partner Agreement."
    examples:
      - name: BillingSubscriptionsListByInvoiceSection
        text: |-
               az billing subscription list --account-name "{billingAccountName}" --profile-name \
"{billingProfileName}" --invoice-section-name "{invoiceSectionName}"
"""

helps['billing subscription show'] = """
    type: command
    short-summary: "Gets a subscription by its ID. The operation is supported for billing accounts with agreement type \
Microsoft Customer Agreement and Microsoft Partner Agreement."
    examples:
      - name: BillingSubscription
        text: |-
               az billing subscription show --account-name "{billingAccountName}"
"""

helps['billing subscription update'] = """
    type: command
    short-summary: "Updates the properties of a billing subscription. Currently, cost center can be updated. The \
operation is supported only for billing accounts with agreement type Microsoft Customer Agreement."
    examples:
      - name: UpdateBillingProperty
        text: |-
               az billing subscription update --account-name "{billingAccountName}" --cost-center "ABC1234"
"""

helps['billing subscription move'] = """
    type: command
    short-summary: "Moves a subscription's charges to a new invoice section. The new invoice section must belong to \
the same billing profile as the existing invoice section. This operation is supported for billing accounts with \
agreement type Microsoft Customer Agreement."
    examples:
      - name: MoveBillingSubscription
        text: |-
               az billing subscription move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}"
"""

helps['billing subscription validate-move'] = """
    type: command
    short-summary: "Validates if a subscription's charges can be moved to a new invoice section. This operation is \
supported for billing accounts with agreement type Microsoft Customer Agreement."
    examples:
      - name: SubscriptionMoveValidateFailure
        text: |-
               az billing subscription validate-move --account-name "{billingAccountName}" \
--destination-invoice-section-id "/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{bi\
llingProfileName}/invoiceSections/{newInvoiceSectionName}"
      - name: SubscriptionMoveValidateSuccess
        text: |-
               az billing subscription validate-move --account-name "{billingAccountName}" \
--destination-invoice-section-id "/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{bi\
llingProfileName}/invoiceSections/{newInvoiceSectionName}"
"""

helps['billing subscription wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the billing subscription is met.
    examples:
      - name: Pause executing next line of CLI script until the billing subscription is successfully created.
        text: |-
               az billing subscription wait --account-name "{billingAccountName}" --created
"""

helps['billing product'] = """
    type: group
    short-summary: billing product
"""

helps['billing product list'] = """
    type: command
    short-summary: "Lists the products for a billing account. These don't include products billed based on usage. The \
operation is supported for billing accounts with agreement type Microsoft Customer Agreement or Microsoft Partner \
Agreement."
    examples:
      - name: ProductsListByInvoiceSection
        text: |-
               az billing product list --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--invoice-section-name "{invoiceSectionName}"
"""

helps['billing product show'] = """
    type: command
    short-summary: "Gets a product by ID. The operation is supported only for billing accounts with agreement type \
Microsoft Customer Agreement."
    examples:
      - name: Product
        text: |-
               az billing product show --account-name "{billingAccountName}" --name "{productName}"
"""

helps['billing product update'] = """
    type: command
    short-summary: "Updates the properties of a Product. Currently, auto renew can be updated. The operation is \
supported only for billing accounts with agreement type Microsoft Customer Agreement."
    examples:
      - name: UpdateBillingProperty
        text: |-
               az billing product update --account-name "{billingAccountName}" --auto-renew "Off" --name \
"{productName}"
"""

helps['billing product move'] = """
    type: command
    short-summary: "Moves a product's charges to a new invoice section. The new invoice section must belong to the \
same billing profile as the existing invoice section. This operation is supported only for products that are purchased \
with a recurring charge and for billing accounts with agreement type Microsoft Customer Agreement."
    examples:
      - name: MoveProduct
        text: |-
               az billing product move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}" --name "{productName}"
"""

helps['billing product validate-move'] = """
    type: command
    short-summary: "Validates if a product's charges can be moved to a new invoice section. This operation is \
supported only for products that are purchased with a recurring charge and for billing accounts with agreement type \
Microsoft Customer Agreement."
    examples:
      - name: SubscriptionMoveValidateFailure
        text: |-
               az billing product validate-move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}" --name "{productName}"
      - name: SubscriptionMoveValidateSuccess
        text: |-
               az billing product validate-move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}" --name "{productName}"
"""

helps['billing invoice'] = """
    type: group
    short-summary: billing invoice
"""

helps['billing invoice list'] = """
    type: command
    short-summary: "Lists the invoices for a subscription."
    examples:
      - name: InvoicesListByBillingProfile
        text: |-
               az billing invoice list --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--period-end-date "2018-06-30" --period-start-date "2018-01-01"
      - name: InvoicesListByBillingProfileWithRebillDetails
        text: |-
               az billing invoice list --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--period-end-date "2018-06-30" --period-start-date "2018-01-01"
"""

helps['billing invoice show'] = """
    type: command
    short-summary: "Gets an invoice. The operation is supported for billing accounts \
with agreement type Microsoft Partner Agreement or Microsoft Customer Agreement."
    examples:
      - name: Show an invoice by billing account name and ID
        text: |-
               az billing invoice show --account-name "{billingAccountName}" --name "{invoiceName}"
      - name: Show an invoice by ID
        text: |-
               az billing invoice show --name "{invoiceName}"
      - name: Show an invoice by subscription ID and invoice ID
        text: |-
               az billing invoice show --name "{invoiceName}" --by-subscription
"""

helps['billing invoice download'] = """
    type: command
    short-summary: "Get URL to download invoice"
    examples:
      - name: Get a URL to download an invoice. The operation is supported for billing accounts with agreement type Microsoft Partner Agreement or Microsoft Customer Agreement.
        text: |-
               az billing invoice download --account-name "{billingAccountName}" --invoice-name "{invoiceName}" --download-token "{downloadToken}"
      - name: Get a URL to download an multiple invoices documents (invoice pdf, tax receipts, credit notes) as a zip file. The operation is supported for billing accounts with agreement type Microsoft Partner Agreement or Microsoft Customer Agreement.
        text: |-
               az billing invoice download --account-name "{billingAccountName}" --download-urls "{ListOfDownloadURLs}"
      - name: Gets a URL to download multiple invoices documents (invoice pdf, tax receipts, credit notes) as a zip file.
        text: |-
               az billing invoice download --download-urls "{ListOfDownloadURLs}"
      - name: Gets a URL to download an invoice.
        text: |-
               az billing invoice download --invoice-name "{invoiceName}" --download-token "{downloadToken}"
"""

helps['billing transaction'] = """
    type: group
    short-summary: billing transaction
"""

helps['billing transaction list'] = """
    type: command
    short-summary: "Lists the transactions for an invoice. Transactions include purchases, refunds and Azure usage \
charges."
    examples:
      - name: TransactionsListByInvoice
        text: |-
               az billing transaction list --account-name "{billingAccountName}" --invoice-name "{invoiceName}"
"""

helps['billing policy'] = """
    type: group
    short-summary: billing policy
"""

helps['billing policy show'] = """
    type: command
    short-summary: Show the policies for a customer or for a billing profile. This operation is supported only for billing accounts with \
agreement type Microsoft Partner Agreement."
    examples:
      - name: Lists the policies for a customer
        text: |-
               az billing policy show --account-name "{billingAccountName}" --customer-name "{customerName}"
      - name: Lists the policies for a billing profile
        text: |-
               az billing policy show --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
"""

helps['billing policy update'] = """
    type: command
    short-summary: "Updates the policies for a billing profile. This operation is supported only for billing accounts \
with agreement type Microsoft Customer Agreement."
    examples:
      - name: UpdatePolicy
        text: |-
               az billing policy update --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--marketplace-purchases "OnlyFreeAllowed" --reservation-purchases "NotAllowed" --view-charges "Allowed"
"""

helps['billing property'] = """
    type: group
    short-summary: billing property
"""

helps['billing property show'] = """
    type: command
    short-summary: "Get the billing properties for a subscription. This operation is not supported for billing \
accounts with agreement type Enterprise Agreement."
    examples:
      - name: BillingProperty
        text: |-
               az billing property show
"""

helps['billing property update'] = """
    type: command
    short-summary: "Updates the billing property of a subscription. Currently, cost center can be updated. The \
operation is supported only for billing accounts with agreement type Microsoft Customer Agreement."
    examples:
      - name: UpdateBillingProperty
        text: |-
               az billing property update --cost-center "1010"
"""
