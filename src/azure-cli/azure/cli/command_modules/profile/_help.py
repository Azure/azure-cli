# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from knack.help_files import helps  # pylint: disable=unused-import

helps['login'] = """
type: command
short-summary: Log in to Azure.
examples:
- name: Log in interactively.
  text: az login
- name: Log in with user name and password. This doesn't work with Microsoft accounts or accounts that have two-factor authentication enabled.
  text: az login --user johndoe@contoso.com --password VerySecret
- name: Log in with a password containing a `-` as the first character.
  text: az login --user johndoe@contoso.com --password=-myPasswordThatStartsWithAdash
- name: Log in with a service principal using a client secret.
  text: az login --service-principal --user http://azure-cli-2016-08-05-14-31-15 --password VerySecret --tenant contoso.onmicrosoft.com
- name: Log in with a service principal using a client certificate.
  text: aaz login --service-principal --user http://azure-cli-2016-08-05-14-31-15 --password ~/MyCertfile.pem --tenant contoso.onmicrosoft.com
- name: Log in using a VM's system assigned identity.
  text: az login --identity
- name: Log in using a VM's user assigned identity. Client or object ids of the service identity also work.
  text: az login --identity --user /subscriptions/MySubscriptionID/resourcegroups/MyResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myID
"""

helps['account'] = """
type: group
short-summary: Manage Azure subscription information.
long-summary: >
    Use `az login` to log into Azure before managing subscriptions.
    For an in-depth overview of working with subscriptions using the Azure CLI, see
    [How to manage Azure subscriptions with the Azure CLI](https://learn.microsoft.com/cli/azure/manage-azure-subscriptions-azure-cli).
"""

helps['account clear'] = """
type: command
short-summary: Clear all subscriptions from the CLI's local cache.
long-summary: To clear the current subscription, use `az logout`.
"""

helps['account list'] = """
type: command
short-summary: Get a list of subscriptions for the logged in account.
examples:
- name: List all subscriptions.
  text: az account list --all
- name: List all enabled subscriptions.
  text: az account list
- name: Get the current default subscription.
  text: az account list --query "[?isDefault]"
- name: Refresh the list of subscriptions.
  text: az account list --refresh
"""

helps['account list-locations'] = """
type: command
short-summary: List supported regions for the current subscription.
"""

helps['account show'] = """
type: command
short-summary: Get the details of a subscription.
long-summary: If no subscription is specified, information for the current subscription is returned.
examples:
- name: Get the current default subscription returning results in your default format.
  text: az account show
- name: Get information about a named subscription returning results as a table. Use `--output yaml` for plain text.
  text: az account show --name "My subscription name" --output table
- name: Get information about a subscription using the subscription ID.
  text: az account show --name MySubscriptionID
- name: >
    Get specific information about a subscription using `--query`.
    To see available query options, first run `az account show --output json`.
    For in-depth `--query` examples see [How to query Azure CLI command output using a JMESPath query](https://learn.microsoft.com/cli/azure/query-azure-cli).
  text: >
    az account show --query name
    az account show --query user.name
- name: Return results in plain text.
  text: az account show --query MyTenantID --output tsv
- name: Store the default subscription ID in a variable.
  text: >
    # Bash script
    subscriptionId="$(az account show --query id --output tsv)"
    echo "The current subscription ID is $subscriptionId"
"""

helps['account set'] = """
type: command
short-summary: Change the active subscription.
examples:
- name: Change the active subscription using a subscription name
  text: az account set --subscription "My subscription name"
- name: Change the active subscription using a subscription ID
  text: az account set --subscription MySubscriptionID
- name: Change the active subscription using a variable.
  text: >
    # Bash script
    subscriptionId="$(az account list --query "[?contains(name, 'OneOfMySubscriptionNames')].id" --output tsv)"
    az account set --subscription $subscriptionId
    echo "The current subscription has been set to $subscriptionId"
"""

helps['account get-access-token'] = """
type: command
short-summary: Get a token for utilities to access Azure.
long-summary: >
    The token will be valid for at least 5 minutes with a maximum of 60 minutes.
    If the subscription argument isn't specified, the current account is used.
examples:
- name: Get an access token information for the current account.
  text: az account get-access-token
- name: Get an access token information for a specific subscription.
  text: az account get-access-token --subscription MySubscriptionID
- name: Get an access token information for a specific tenant.
  text: az account get-access-token --tenant MySubscriptionID
- name: Get an access token information to use with MS Graph API.
  text: az account get-access-token --resource-type ms-graph
- name: Get an access token information for a particular resource. If you receive a `Failed to connect to MSI...` error, your resource may not exist.
  text: >
    az account get-access-token --resource MyResourceID
    az account get-access-token --resource https://database.windows.net/
- name: Get only the access token for a particular resource returning results in plain text. This script is useful when you want to store the token in a variable.
  text: az account get-access-token --resource https://management.core.windows.net/ --query accessToken --output tsv
- name: Get an access token for a particular scope
  text: az account get-access-token --scope https://management.azure.com//.default
"""

helps['self-test'] = """
type: command
short-summary: Runs a self-test of the CLI.
"""
