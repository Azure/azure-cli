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
    - name: Log in with user name and password. This doesn't work with Microsoft accounts or accounts that have two-factor authentication enabled. Use -p=secret if the first character of the password is '-'.
      text: az login -u johndoe@contoso.com -p VerySecret
    - name: Log in with a service principal using client secret. Use -p=secret if the first character of the password is '-'.
      text: az login --service-principal -u http://azure-cli-2016-08-05-14-31-15 -p VerySecret --tenant contoso.onmicrosoft.com
    - name: Log in with a service principal using client certificate.
      text: az login --service-principal -u http://azure-cli-2016-08-05-14-31-15 -p ~/mycertfile.pem --tenant contoso.onmicrosoft.com
    - name: Log in using a VM's system-assigned managed identity.
      text: az login --identity
    - name: Log in using a VM's user-assigned managed identity. Client or object ids of the service identity also work.
      text: az login --identity -u /subscriptions/<subscriptionId>/resourcegroups/myRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myID
    - name: Log in using EnvironmentCredential and a service principal.
      text: |-
        # Bash script
        export AZURE_TENANT_ID='<tenant ID>'
        export AZURE_CLIENT_ID='<service principal appId>'
        export AZURE_CLIENT_SECRET='<service principal secret>'
        az login --environment
    - name: Log in using EnvironmentCredential and a user account.
      text: |-
        # Bash script
        # AZURE_CLIENT_ID defaults to Azure CLI's client ID
        # export AZURE_CLIENT_ID='04b07795-8ddb-461a-bbee-02f9e1bf7b46'
        export AZURE_USERNAME='<tenant ID>'
        export AZURE_PASSWORD='<service principal appId>'
        az login --environment
"""

helps['account'] = """
type: group
short-summary: Manage Azure subscription information.
"""

helps['account clear'] = """
type: command
short-summary: Clear all subscriptions from the CLI's local cache.
long-summary: To clear the current subscription, use 'az logout'.
"""

helps['account list'] = """
type: command
short-summary: Get a list of subscriptions for the logged in account.
"""

helps['account list-locations'] = """
type: command
short-summary: List supported regions for the current subscription.
"""

helps['account show'] = """
type: command
short-summary: Get the details of a subscription.
long-summary: If no subscription is specified, shows the current subscription.
"""

helps['account set'] = """
type: command
short-summary: Set a subscription to be the current active subscription.
"""

helps['account show'] = """
type: command
short-summary: Get the details of a subscription.
long-summary: >-
    If the subscription isn't specified, shows the details of the default subscription.


    When --sdk-auth is used,
    the output includes credentials that you must protect. Be sure that you do not include these credentials
    in your code or check the credentials into your source control. As an alternative, consider using
    [managed identities](https://aka.ms/azadsp-managed-identities) if available to avoid the need to use credentials.
"""

helps['account get-access-token'] = """
type: command
short-summary: Get a token for utilities to access Azure.
long-summary: >
    The token will be valid for at least 5 minutes with the maximum at 60 minutes.
    If the subscription argument isn't specified, the current account is used.
examples:
    - name: Get an access token for the current account
      text: >
        az account get-access-token
    - name: Get an access token for a specific subscription
      text: >
        az account get-access-token --subscription 00000000-0000-0000-0000-000000000000
    - name: Get an access token for a specific tenant
      text: >
        az account get-access-token --tenant 00000000-0000-0000-0000-000000000000
    - name: Get an access token to use with MS Graph API
      text: >
        az account get-access-token --resource-type ms-graph
"""

helps['account export-msal-cache'] = """
type: command
short-summary: Export MSAL cache, by default to `~/.azure/msal.cache.snapshot.json`.
long-summary: >
    The exported cache is unencrypted. It contains login information of all logged-in users. Make sure you protect
    it safely.
    
    You can mount the exported MSAL cache to a container at `~/.IdentityService/msal.cache`, so that Azure CLI
    inside the container can automatically authenticate.
examples:
    - name: Export MSAL cache to the default path.
      text: az account export-msal-cache
    - name: Export MSAL cache to a custom path.
      text: az account export-msal-cache --path ~/msal_cache.json
"""

helps['self-test'] = """
type: command
short-summary: Runs a self-test of the CLI.
"""
