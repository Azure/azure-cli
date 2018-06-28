# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['ad sp create-for-rbac'] = """
    type: command
    short-summary: Create a service principal and configure its access to Azure resources.
    parameters:
        - name: --name -n
          short-summary: Name or app URI to associate the RBAC with. If not present, a name will be generated.
        - name: --password -p
          short-summary: The password used to log in.
          long-summary: If not present and `--cert` is not specified, a random password will be generated.
        - name: --cert
          short-summary: Certificate to use for credentials.
          long-summary: When used with `--keyvault,` indicates the name of the cert to use or create.
            Otherwise, supply a PEM or DER formatted public certificate string. Use `@{file}` to
            load from a file. Do not include private key info.
        - name: --create-cert
          short-summary: Create a self-signed certificate to use for the credential.
          long-summary: Use with `--keyvault` to create the certificate in Key Vault. Otherwise, a
            certificate will be created locally.
        - name: --keyvault
          short-summary: Name or ID of a KeyVault to use for creating or retrieving certificates.
        - name: --years
          short-summary: 'Number of years for which the credentials will be valid. Default: 1 year'
        - name: --scopes
          short-summary: >
            Space-separated list of scopes the service principal's role assignment applies to.
            Defaults to the root of the current subscription.
        - name: --role
          short-summary: Role of the service principal.
    examples:
        - name: Create with a default role assignment.
          text: >
            az ad sp create-for-rbac
        - name: Create using a custom name, and with a default assignment.
          text: >
            az ad sp create-for-rbac -n "MyApp"
        - name: Create without a default assignment.
          text: >
            az ad sp create-for-rbac --skip-assignment
        - name: Create with customized contributor assignments.
          text: |
            az ad sp create-for-rbac -n "MyApp" --role contributor \\
                --scopes /subscriptions/{SubID}/resourceGroups/{ResourceGroup1} \\
                /subscriptions/{SubID}/resourceGroups/{ResourceGroup2}
        - name: Create using a self-signed certificte.
          text: az ad sp create-for-rbac --create-cert
        - name: Create using a self-signed certificate, and store it within KeyVault.
          text: az ad sp create-for-rbac --keyvault MyVault --cert CertName --create-cert
        - name: Create using existing certificate in KeyVault.
          text: az ad sp create-for-rbac --keyvault MyVault --cert CertName
    """

helps['ad sp credential'] = """
    type: group
    short-summary: manage a service principal's credentials.
"""

helps['ad sp credential list'] = """
    type: command
    short-summary: list a service principal's credentials.
"""

helps['ad sp credential delete'] = """
    type: command
    short-summary: delete a service principal's credential.
"""

helps['ad sp credential reset'] = """
    type: command
    short-summary: Reset a service principal credential.
    long-summary: Use upon expiration of the service principal's credentials, or in the event that login credentials are lost.
    parameters:
        - name: --name -n
          short-summary: Name or app URI for the credential.
        - name: --password -p
          short-summary: The password used to log in.
          long-summary: If not present and `--cert` is not specified, a random password will be generated.
        - name: --cert
          short-summary: Certificate to use for credentials.
          long-summary: When using `--keyvault,` indicates the name of the cert to use or create.
            Otherwise, supply a PEM or DER formatted public certificate string. Use `@{file}` to
            load from a file. Do not include private key info.
        - name: --create-cert
          short-summary: Create a self-signed certificate to use for the credential.
          long-summary: Use with `--keyvault` to create the certificate in Key Vault. Otherwise, a
            certificate will be created locally.
        - name: --keyvault
          short-summary: Name or ID of a KeyVault to use for creating or retrieving certificates.
        - name: --years
          short-summary: 'Number of years for which the credentials will be valid. Default: 1 year'
"""
helps['ad sp delete'] = """
    type: command
    short-summary: Delete a service principal and its role assignments.
"""
helps['ad sp create'] = """
    type: command
    short-summary: Create a service principal.
"""
helps['ad sp list'] = """
    type: command
    short-summary: List service principals.
"""
helps['ad sp show'] = """
    type: command
    short-summary: Get the details of a service principal.
"""
helps['ad app'] = """
    type: group
    short-summary: Manage applications with AAD Graph.
"""
helps['ad app delete'] = """
    type: command
    short-summary: Delete an application.
"""
helps['ad app list'] = """
    type: command
    short-summary: List applications.
"""
helps['ad app show'] = """
    type: command
    short-summary: Get the details of an application.
"""
helps['ad app update'] = """
    type: command
    short-summary: Update an application.
    examples:
        - name: update a native application with delegated permission of "access the AAD directory as the signed-in user"
          text: |
                az ad app update --id e042ec79-34cd-498f-9d9f-123456781234 --required-resource-accesses @manifest.json
                ("manifest.json" contains the following content)
                [{
                    "resourceAppId": "00000002-0000-0000-c000-000000000000",
                    "resourceAccess": [
                        {
                            "id": "a42657d6-7f20-40e3-b6f0-cee03008a62a",
                            "type": "Scope"
                        }
                   ]
                }]
        - name: update an application's group membership claims to "All"
          text: >
                az ad app update --id e042ec79-34cd-498f-9d9f-123456781234 --set groupMembershipClaims=All

"""
helps['ad user list'] = """
    type: command
    short-summary: List Azure Active Directory users.
"""
helps['role'] = """
    type: group
    short-summary: Manage user roles for access control with Azure Active Directory and service principals.
"""
helps['role assignment'] = """
    type: group
    short-summary: Manage role assignments.
"""
helps['role assignment create'] = """
    type: command
    short-summary: Create a new role assignment for a user, group, or service principal.
    examples:
        - name: Create role assignment for an assignee.
          text: az role assignment create --assignee sp_name --role a_role
"""
helps['role assignment delete'] = """
    type: command
    short-summary: Delete role assignments.
"""
helps['role assignment list'] = """
    type: command
    short-summary: List role assignments.
    long-summary: By default, only assignments scoped to subscription will be displayed. To view assignments scoped by resource or group, use `--all`.
"""
helps['role assignment list-changelogs'] = """
    type: command
    short-summary: List changelogs for role assignments.
"""
helps['role definition'] = """
    type: group
    short-summary: Manage role definitions.
"""

helps['role definition create'] = """
    type: command
    short-summary: Create a custom role definition.
    parameters:
        - name: --role-definition
          type: string
          short-summary: Description of a role as JSON, or a path to a file containing a JSON description.
    examples:
        - name: Create a role with read-only access to storage and network resources, and the ability to start or restart VMs.
          text: |
                az role definition create --role-definition '{
                    "Name": "Contoso On-call",
                    "Description": "Perform VM actions and read storage and network information."
                    "Actions": [
                        "Microsoft.Compute/*/read",
                        "Microsoft.Compute/virtualMachines/start/action",
                        "Microsoft.Compute/virtualMachines/restart/action",
                        "Microsoft.Network/*/read",
                        "Microsoft.Storage/*/read",
                        "Microsoft.Authorization/*/read",
                        "Microsoft.Resources/subscriptions/resourceGroups/read",
                        "Microsoft.Resources/subscriptions/resourceGroups/resources/read",
                        "Microsoft.Insights/alertRules/*",
                        "Microsoft.Support/*"
                    ],
                    "DataActions": [
                        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/*"
                    ],
                    "NotDataActions": [
                        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write"
                    ],
                    "AssignableScopes": ["/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"]
                }'
        - name: Create a role from a file containing a JSON description.
          text: >
            az role definition create --role-definition @ad-role.json
"""

helps['role definition delete'] = """
    type: command
    short-summary: Delete a role definition.
"""
helps['role definition list'] = """
    type: command
    short-summary: List role definitions.
"""
helps['role definition update'] = """
    type: command
    short-summary: Update a role definition.
    parameters:
        - name: --role-definition
          type: string
          short-summary: Description of a role as JSON, or a path to a file containing a JSON description.
"""
helps['ad'] = """
    type: group
    short-summary: Manage Azure Active Directory Graph entities needed for Role Based Access Control
"""
helps['ad app create'] = """
    type: command
    short-summary: Create a web application, web API or native application
    examples:
        - name: Create a native application with delegated permission of "access the AAD directory as the signed-in user"
          text: |
                az ad app create --display-name my-native --native-app --required-resource-accesses @manifest.json
                ("manifest.json" contains the following content)
                [{
                    "resourceAppId": "00000002-0000-0000-c000-000000000000",
                    "resourceAccess": [
                        {
                            "id": "a42657d6-7f20-40e3-b6f0-cee03008a62a",
                            "type": "Scope"
                        }
                   ]
                }]
"""
helps['ad group'] = """
    type: group
    short-summary: Manage Azure Active Directory groups.
"""
helps['ad group create'] = """
    type: command
    short-summary: Create a group in the directory.
"""
helps['ad group member'] = """
    type: group
    short-summary: Manage Azure Active Directory group members.
"""
helps['ad group member check'] = """
    type: command
    short-summary: Check if a member is in a group.
"""
helps['ad sp'] = """
    type: group
    short-summary: Manage Azure Active Directory service principals for automation authentication.
"""
helps['ad user'] = """
    type: group
    short-summary: Manage Azure Active Directory users and user authentication.
"""
