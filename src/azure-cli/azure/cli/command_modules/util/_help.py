# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines, anomalous-backslash-in-string

helps['rest'] = """
type: command
short-summary: Invoke a custom request.
long-summary: >
    This command automatically authenticates using the logged-in credential: If Authorization header is not set, it
    attaches header `Authorization: Bearer <token>`, where `<token>` is retrieved from AAD. The target resource of the
    token is derived from --url if --url starts with an endpoint from `az cloud show --query endpoints`. You may also
    use --resource for a custom resource.


    If Content-Type header is not set and --body is a valid JSON string, Content-Type header will default to
    application/json.


    For passing JSON in PowerShell, see https://github.com/Azure/azure-cli/blob/dev/doc/quoting-issues-with-powershell.md
examples:
  - name: Get Audit log through Microsoft Graph
    text: >
        az rest --method get --url https://graph.microsoft.com/beta/auditLogs/directoryAudits
  - name: Update a Azure Active Directory Graph User's display name
    text: |
        (Bash or CMD)
        az rest --method patch --url "https://graph.microsoft.com/v1.0/users/johndoe@azuresdkteam.onmicrosoft.com" --body "{\\"displayName\\": \\"johndoe2\\"}"

        (Bash)
        az rest --method patch --url "https://graph.microsoft.com/v1.0/users/johndoe@azuresdkteam.onmicrosoft.com" --body '{"displayName": "johndoe2"}'

        (PowerShell)
        az rest --method patch --url "https://graph.microsoft.com/v1.0/users/johndoe@azuresdkteam.onmicrosoft.com" --body '{\\"displayName\\": \\"johndoe2\\"}'
  - name: Get a virtual machine
    text: >
        az rest --method get --uri /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Compute/virtualMachines/{vmName}?api-version=2019-03-01
  - name: Create a public IP address from body.json file
    text: >
        az rest --method put --url https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/publicIPAddresses/{publicIpAddressName}?api-version=2019-09-01 --body @body.json
  - name: List the top three resources (Bash)
    text: >
        az rest --method get --url https://management.azure.com/subscriptions/{subscriptionId}/resources?api-version=2019-07-01 --url-parameters \\$top=3
"""

helps['version'] = """
type: command
short-summary: Show the versions of Azure CLI modules and extensions in JSON format by default or format configured by --output
"""

helps['upgrade'] = """
type: command
short-summary: Upgrade Azure CLI and extensions
"""

helps['demo'] = """
type: group
short-summary: Demos for designing, developing and demonstrating Azure CLI.
"""

helps['demo style'] = """
type: command
short-summary: A demo showing supported text styles.
"""

helps['demo secret-store'] = """
type: group
short-summary: A demo showing how to use secret store.
"""

helps['demo secret-store save'] = """
type: command
short-summary: Save custom data to secret store.
examples:
  - name: Save data to secret store.
    text: az demo secret-store save "name=Johann Sebastian Bach" job=musician
"""

helps['demo secret-store load'] = """
type: command
short-summary: Load custom data from secret store.
"""
