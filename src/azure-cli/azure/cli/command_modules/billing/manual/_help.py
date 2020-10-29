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
    short-summary: "List the billing accounts that a user has access to."
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
    short-summary: "Get a billing account by its ID."
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
    short-summary: "Update the properties of a billing account. Currently, displayName and address can be updated. \
The operation is supported only for billing accounts with agreement type Microsoft Customer Agreement."
    parameters:
      - name: --sold-to
        short-summary: "The address of the individual or organization that is responsible for the billing account."
        long-summary: |
            Usage: --sold-to first-name=XX last-name=XX company-name=XX address-line1=XX address-line2=XX \
address-line3=XX city=XX district=XX region=XX country=XX postal-code=XX email=XX phone-number=XX
    examples:
      - name: Update a billing account
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
      - name: Show the balance of a billing profile
        text: |-
               az billing balance show --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
"""

helps['billing instruction'] = """
    type: group
    short-summary: Manage billing instruction
"""

helps['billing instruction list'] = """
    type: command
    short-summary: "List the instructions by billing profile id."
    examples:
      - name: List instructions by billing profile
        text: |-
               az billing instruction list --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
"""

helps['billing instruction show'] = """
    type: command
    short-summary: "Show the instruction by name. These are custom billing instructions and are only applicable for \
certain customers."
    examples:
      - name: Instruction
        text: |-
               az billing instruction show --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--name "{instructionName}"
"""

helps['billing instruction create'] = """
    type: command
    short-summary: "Create an instruction. These are custom billing instructions and are only applicable \
for certain customers."
    examples:
      - name: Create an instruction
        text: |-
               az billing instruction create --account-name "{billingAccountName}" --profile-name \
"{billingProfileName}" --name "{instructionName}" --amount 5000 --end-date "2020-12-30T21:26:47.997Z" --start-date \
"2019-12-30T21:26:47.997Z"
"""

helps['billing instruction update'] = """
    type: command
    short-summary: "Update an instruction. These are custom billing instructions and are only applicable \
for certain customers."
    examples:
      - name: Create an instruction
        text: |-
               az billing instruction update --account-name "{billingAccountName}" --profile-name "{billingProfileName}" --name "{instructionName}" --amount 5000
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
    short-summary: "List the customers that are billed to a billing account. The operation is supported only for \
billing accounts with agreement type Microsoft Partner Agreement."
    examples:
      - name: List customers by billing account
        text: |-
               az billing customer list --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
"""

helps['billing customer show'] = """
    type: command
    short-summary: "Get a customer by its ID. The operation is supported only for billing accounts with agreement \
type Microsoft Partner Agreement."
    examples:
      - name: Show a customer with default properties
        text: |-
               az billing customer show --account-name "{billingAccountName}" --name "{customerName}"
      - name: Show a customer with desired expanded properties
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
    short-summary: "List the invoice sections that a user has access to. The operation is supported only for billing \
accounts with agreement type Microsoft Customer Agreement."
    examples:
      - name: List invoice sections by billing account and billing profile
        text: |-
               az billing invoice section list --account-name "{billingAccountName}" --profile-name \
"{billingProfileName}"
"""

helps['billing invoice section show'] = """
    type: command
    short-summary: "Get an invoice section by its ID. The operation is supported only for billing accounts with \
agreement type Microsoft Customer Agreement."
    examples:
      - name: Show an invoice section
        text: |-
               az billing invoice section show --account-name "{billingAccountName}" --profile-name \
"{billingProfileName}" --name "{invoiceSectionName}"
"""

helps['billing invoice section create'] = """
    type: command
    short-summary: "Creates or updates an invoice section. The operation is supported only for billing accounts with \
agreement type Microsoft Customer Agreement."
    examples:
      - name: Create an invoice section
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

helps['billing permission'] = """
    type: group
    short-summary: List billing permissions
"""

helps['billing permission list'] = """
    type: command
    short-summary: "List the billing permissions the caller has on a billing account."
    examples:
      - name: List permissions by billing account scope
        text: |-
               az billing permission list --account-name "{billingAccountName}"
      - name: List permissions by billing profile scope
        text: |-
               az billing permission list --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
      - name: List permission by invoice section scope
        text: |-
               az billing permission list --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--invoice-section-name "{invoiceSectionName}"
      - name: List permissions by customer scope
        text: |-
               az billing permission list --account-name "{billingAccountName}" --customer-name "{customerName}"
"""

helps['billing subscription'] = """
    type: group
    short-summary: billing subscription
"""

helps['billing subscription list'] = """
    type: command
    short-summary: "List the subscriptions for a billing account. The operation is supported for billing accounts \
with agreement type Microsoft Customer Agreement or Microsoft Partner Agreement."
    examples:
      - name: List subscriptions for an invoice section
        text: |-
               az billing subscription list --account-name "{billingAccountName}" --profile-name \
"{billingProfileName}" --invoice-section-name "{invoiceSectionName}"
"""

helps['billing subscription show'] = """
    type: command
    short-summary: "Get a subscription by its ID. The operation is supported for billing accounts with agreement type \
Microsoft Customer Agreement and Microsoft Partner Agreement."
    examples:
      - name: Show the subscription information of a billing account
        text: |-
               az billing subscription show --account-name "{billingAccountName}"
"""

helps['billing subscription update'] = """
    type: command
    short-summary: "Update the properties of a billing subscription. Currently, cost center can be updated. The \
operation is supported only for billing accounts with agreement type Microsoft Customer Agreement."
    examples:
      - name: Update properties of a billing account
        text: |-
               az billing subscription update --account-name "{billingAccountName}" --cost-center "ABC1234"
"""

helps['billing subscription move'] = """
    type: command
    short-summary: "Moves a subscription's charges to a new invoice section. The new invoice section must belong to \
the same billing profile as the existing invoice section. This operation is supported for billing accounts with \
agreement type Microsoft Customer Agreement."
    examples:
      - name: Move a subscription to another invoice section
        text: |-
               az billing subscription move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}"
"""

helps['billing subscription validate-move'] = """
    type: command
    short-summary: "Validate if a subscription's charges can be moved to a new invoice section. This operation is \
supported for billing accounts with agreement type Microsoft Customer Agreement."
    examples:
      - name: Validate whether a move for subscription to another invoice section is valid or not
        text: |-
               az billing subscription validate-move --account-name "{billingAccountName}" \
--destination-invoice-section-id "/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{bi\
llingProfileName}/invoiceSections/{newInvoiceSectionName}"
      - name: Validate whether a move for subscription to another invoice section is valid or not
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
    short-summary: "List the products for a billing account. These don't include products billed based on usage. The \
operation is supported for billing accounts with agreement type Microsoft Customer Agreement or Microsoft Partner \
Agreement."
    examples:
      - name: List products by invoice name
        text: |-
               az billing product list --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--invoice-section-name "{invoiceSectionName}"
"""

helps['billing product show'] = """
    type: command
    short-summary: "Get a product by ID. The operation is supported only for billing accounts with agreement type \
Microsoft Customer Agreement."
    examples:
      - name: Shgow a product information
        text: |-
               az billing product show --account-name "{billingAccountName}" --name "{productName}"
"""

helps['billing product update'] = """
    type: command
    short-summary: "Update the properties of a Product. Currently, auto renew can be updated. The operation is \
supported only for billing accounts with agreement type Microsoft Customer Agreement."
    examples:
      - name: Update properties of a product
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
      - name: Move a product's charges to a new invoice section
        text: |-
               az billing product move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}" --name "{productName}"
"""

helps['billing product validate-move'] = """
    type: command
    short-summary: "Validate if a product's charges can be moved to a new invoice section. This operation is \
supported only for products that are purchased with a recurring charge and for billing accounts with agreement type \
Microsoft Customer Agreement."
    examples:
      - name: Validate if a product's charges can be moved to a new invoice section
        text: |-
               az billing product validate-move --account-name "{billingAccountName}" --destination-invoice-section-id \
"/providers/Microsoft.Billing/billingAccounts/{billingAccountName}/billingProfiles/{billingProfileName}/invoiceSections\
/{newInvoiceSectionName}" --name "{productName}"
      - name: Validate if a product's charges can be moved to a new invoice section
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
    short-summary: "List the invoices for a subscription."
    examples:
      - name: List invoices by billing account and profile name with default properties
        text: |-
               az billing invoice list --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--period-end-date "2018-06-30" --period-start-date "2018-01-01"
      - name: List invoices by billing account and profile name with expanded properties
        text: |-
               az billing invoice list --account-name "{billingAccountName}" --profile-name "{billingProfileName}" \
--period-end-date "2018-06-30" --period-start-date "2018-01-01"
"""

helps['billing invoice show'] = """
    type: command
    short-summary: "Get an invoice. The operation is supported for billing accounts \
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
      - name: Get a URL to download multiple invoices documents (invoice pdf, tax receipts, credit notes) as a zip file.
        text: |-
               az billing invoice download --download-urls "{ListOfDownloadURLs}"
      - name: Get a URL to download an invoice.
        text: |-
               az billing invoice download --invoice-name "{invoiceName}" --download-token "{downloadToken}"
"""

helps['billing transaction'] = """
    type: group
    short-summary: billing transaction
"""

helps['billing transaction list'] = """
    type: command
    short-summary: "List the transactions for an invoice. Transactions include purchases, refunds and Azure usage \
charges."
    examples:
      - name: List transactions by invoice
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
      - name: List the policies for a customer
        text: |-
               az billing policy show --account-name "{billingAccountName}" --customer-name "{customerName}"
      - name: List the policies for a billing profile
        text: |-
               az billing policy show --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
"""

helps['billing policy update'] = """
    type: command
    short-summary: "Update the policies for a billing profile. This operation is supported only for billing accounts \
with agreement type Microsoft Customer Agreement."
    examples:
      - name: Update the policy for a billing profile
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
      - name: Show the properties of a billing account
        text: |-
               az billing property show
"""

helps['billing property update'] = """
    type: command
    short-summary: "Update the billing property of a subscription. Currently, cost center can be updated. The \
operation is supported only for billing accounts with agreement type Microsoft Customer Agreement."
    examples:
      - name: Update properties of a billing account
        text: |-
               az billing property update --cost-center "1010"
"""

helps['billing role-definition'] = """
    type: group
    short-summary: Display billing role-definition
"""

helps['billing role-definition list'] = """
    type: command
    short-summary: "List the role definitions for a billing account. The operation is supported for billing accounts \
with agreement type Microsoft Partner Agreement or Microsoft Customer Agreement."
    examples:
      - name: Lists the role definitions for a billing account
        text: |-
               az billing role-definition list --account-name "{billingAccountName}"
      - name: List the role definitions for a billing profile.
        text: |-
               az billing role-definition list --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
      - name: List the role definitions for an invoice section.
        text: |-
               az billing role-definition list --account-name "{billingAccountName}" --profile-name "{billingProfileName}" --invoice-section-name "{invoiceSectionName}"
"""

helps['billing role-definition show'] = """
  type: command
  short-summary: Show the role definition details
  examples:
    - name: Show the definition for a role on a billing account. The operation is supported for billing accounts with agreement type Microsoft Partner Agreement or Microsoft Customer Agreement.
      text: |-
             az billing role-definition show --account-name "{billingAccountName}" --name "{billingRoleDefinitionName}"
    - name: Show the definition for a role on a billing profile. The operation is supported for billing accounts with agreement type Microsoft Partner Agreement or Microsoft Customer Agreement.
      text: |-
             az billing role-definition show --account-name "{billingAccountName}" --profile-name "{billingProfileName}" --name "{billingRoleDefinitionName}"
    - name: Show the definition for a role on an invoice section. The operation is supported only for billing accounts with agreement type Microsoft Customer Agreement
      text: |-
             az billing role-definition show --account-name "{billingAccountName}" --invoice-section-name "{invoiceSectionName}" --name "{billingRoleDefinitionName}"
"""

helps['billing role-assignment'] = """
    type: group
    short-summary: billing role-assignment
"""

helps['billing role-assignment list'] = """
    type: command
    short-summary: "List the role assignments for the caller on a billing account. The operation is supported for \
billing accounts with agreement type Microsoft Partner Agreement or Microsoft Customer Agreement."
    examples:
      - name: List role assignements by billing account scope
        text: |-
               az billing role-assignment list --account-name "{billingAccountName}"
      - name: List role assignments by billing profile scope
        text: |-
               az billing role-assignment list --account-name "{billingAccountName}" --profile-name "{billingProfileName}"
      - name: List role assignments by invoice section scope
        text: |-
               az billing role-assignment list --account-name "{billingAccountName}" --profile-name "{billingProfileName}" --invoice-section-name "{invoiceSectionName}"
"""

helps['billing role-assignment show'] = """
  type: command
  short-summary: Show the role assignment detail for the caller within different scopes. The operation is supported for \
billing accounts with agreement type Microsoft Partner Agreement or Microsoft Customer Agreement.
  examples:
    - name: Show a role assignment for the caller on a billing account
      text: |-
             az billing role-assignment show --account-name "{billingAccountName}" --name "{billingRoleAssignmentName}"
    - name: Show a role assignment for the caller on a billing profile
      text: |-
             az billing role-assignment show --account-name "{billingAccountName}" --profile-name "{billingProfileName}" --name "{billingRoleAssignmentName}"
    - name: Show a role assignment for the caller on an invoice section
      text: |-
             az billing role-assignment show --account-name "{billingAccountName}" --profile-name "{billingProfileName}" --name "{billingRoleAssignmentName}" --invoice-section-name "{invoiceSectionName}"
"""

helps['billing role-assignment delete'] = """
    type: command
    short-summary: "Delete a role assignment for the caller on a billing account. The operation is supported for \
billing accounts with agreement type Microsoft Partner Agreement or Microsoft Customer Agreement."
    examples:
      - name: InvoiceSectionRoleAssignmentDelete
        text: |-
               az billing role-assignment delete --account-name "{billingAccountName}" --profile-name \
"{billingProfileName}" --name "{billingRoleAssignmentName}" --invoice-section-name "{invoiceSectionName}"
"""

helps['billing agreement'] = """
    type: group
    short-summary: Display billing agreement
"""

helps['billing agreement list'] = """
    type: command
    short-summary: "List the agreements for a billing account."
    examples:
      - name: List agreements by billing account
        text: |-
               az billing agreement list --account-name "{billingAccountName}"
"""

helps['billing agreement show'] = """
    type: command
    short-summary: "Get an agreement by ID."
    examples:
      - name: Show an agreement by billing account and its name
        text: |-
               az billing agreement show --name "{agreementName}" --account-name "{billingAccountName}"
"""
