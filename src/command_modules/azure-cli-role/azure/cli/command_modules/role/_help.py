# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["ad"] = """
type: group
short-summary: Manage Azure Active Directory Graph entities needed for Role Based
    Access Control
"""

helps["ad app"] = """
type: group
short-summary: Manage applications with AAD Graph.
"""

helps["ad app create"] = """
type: command
short-summary: Create a web application, web API or native application
examples:
-   name: Create a native application with delegated permission of "access the AAD
        directory as the signed-in user"
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
-   name: Create a web application, web API or native application.
    text: az ad app create --identifier-uris {identifier-uris} --output json --password
        {password} --display-name MyDisplay
    crafted: 'True'
"""

helps["ad app credential"] = """
type: group
short-summary: manage an application's password or certificate credentials
"""

helps["ad app credential delete"] = """
type: command
short-summary: delete an application's password or certificate credentials
"""

helps["ad app credential list"] = """
type: command
short-summary: list an application's password or certificate credentials
"""

helps["ad app credential reset"] = """
type: command
short-summary: append or overwrite an application's password or certificate credentials
"""

helps["ad app delete"] = """
type: command
short-summary: Delete an application.
examples:
-   name: Delete an application.
    text: az ad app delete --id {id}
    crafted: 'True'
"""

helps["ad app list"] = """
type: command
short-summary: List applications.
long-summary: for low latency, by default, only the first 100 will be returned unless
    you provide filter arguments or use "--all"
examples:
-   name: List applications.
    text: az ad app list --output json --query [0]
    crafted: 'True'
"""

helps["ad app owner"] = """
type: group
short-summary: Manage application owners.
"""

helps["ad app owner add"] = """
type: command
short-summary: add an application owner.
"""

helps["ad app owner list"] = """
type: command
short-summary: List application owners.
examples:
-   name: List application owners.
    text: az ad app owner list --id {id}
    crafted: 'True'
"""

helps["ad app owner remove"] = """
type: command
short-summary: remove an application owner.
"""

helps["ad app permission"] = """
type: group
short-summary: manage an application's OAuth2 permissions.
"""

helps["ad app permission add"] = """
type: command
short-summary: add an API permission
long-summary: invoking "az ad app permission grant" is needed to activate it
examples:
-   name: add a Graph API permission of "Sign in and read user profile"
    text: az ad app permission add --id eeba0b46-78e5-4a1a-a1aa-cafe6c123456 --api
        00000002-0000-0000-c000-000000000000 --api-permissions 311a71cc-e848-46a1-bdf8-97ff7156d8e6=Scope
"""

helps["ad app permission delete"] = """
type: command
short-summary: remove an API permission
examples:
-   name: remove an AAD graph permission
    text: az ad app permission delete --id eeba0b46-78e5-4a1a-a1aa-cafe6c123456 --api
        00000002-0000-0000-c000-000000000000
"""

helps["ad app permission grant"] = """
type: command
short-summary: Grant the app an API permission
examples:
-   name: Grant a native application with permissions to access an existing API with
        TTL of 2 years
    text: az ad app permission grant --id e042ec79-34cd-498f-9d9f-1234234 --api a0322f79-57df-498f-9d9f-12678
        --expires 2
"""

helps["ad app permission list"] = """
type: command
short-summary: List API permissions the application has requested
examples:
-   name: List the OAuth2 permissions for an existing AAD app
    text: az ad app permission list --id e042ec79-34cd-498f-9d9f-1234234
"""

helps["ad app show"] = """
type: command
short-summary: Get the details of an application.
examples:
-   name: Get the details of an application.
    text: az ad app show --id {id}
    crafted: 'True'
"""

helps["ad app update"] = """
type: command
short-summary: Update an application.
examples:
-   name: update a native application with delegated permission of "access the AAD
        directory as the signed-in user"
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
-   name: update an application's group membership claims to "All"
    text: >
        az ad app update --id e042ec79-34cd-498f-9d9f-123456781234 --set groupMembershipClaims=All

-   name: Update an application.
    text: az ad app update --set groupMembershipClaims=All --id e042ec79-34cd-498f-9d9f-123456781234
    crafted: 'True'
"""

helps["ad group"] = """
type: group
short-summary: Manage Azure Active Directory groups.
examples:
-   name: Gets group information from the directory.
    text: az ad group show --output json --group {group} --query [0]
    crafted: 'True'
"""

helps["ad group create"] = """
type: command
short-summary: Create a group in the directory.
examples:
-   name: Create a group in the directory.
    text: az ad group create --mail-nickname {mail-nickname} --display-name MyDisplay
    crafted: 'True'
"""

helps["ad group member"] = """
type: group
short-summary: Manage Azure Active Directory group members.
examples:
-   name: Add a member to a group.
    text: az ad group member add --group {group} --member-id {member-id}
    crafted: 'True'
-   name: Gets the members of a group.
    text: az ad group member list --group {group}
    crafted: 'True'
"""

helps["ad group member check"] = """
type: command
short-summary: Check if a member is in a group.
examples:
-   name: Check if a member is in a group.
    text: az ad group member check --group {group} --member-id {member-id}
    crafted: 'True'
"""

helps["ad group owner"] = """
type: group
short-summary: Manage Azure Active Directory group owners.
"""

helps["ad group owner add"] = """
type: command
short-summary: add a group owner.
"""

helps["ad group owner list"] = """
type: command
short-summary: List group owners.
"""

helps["ad group owner remove"] = """
type: command
short-summary: remove a group owner.
"""

helps["ad signed-in-user"] = """
type: group
short-summary: Show graph information about current signed-in user in CLI
"""

helps["ad signed-in-user list-owned-objects"] = """
type: command
short-summary: Get the list of directory objects that are owned by the user
"""

helps["ad sp"] = """
type: group
short-summary: Manage Azure Active Directory service principals for automation authentication.
"""

helps["ad sp create"] = """
type: command
short-summary: Create a service principal.
examples:
-   name: Create a service principal.
    text: az ad sp create --id {id}
    crafted: 'True'
"""

helps["ad sp create-for-rbac"] = """
type: command
short-summary: Create a service principal and configure its access to Azure resources.
parameters:
-   name: --name -n
    short-summary: a URI to use as the logic name. It doesn't need to exist. If not
        present, CLI will generate one.
-   name: --cert
    short-summary: Certificate to use for credentials.
    long-summary: When used with `--keyvault,` indicates the name of the cert to use
        or create. Otherwise, supply a PEM or DER formatted public certificate string.
        Use `@{path}` to load from a file. Do not include private key info.
-   name: --create-cert
    short-summary: Create a self-signed certificate to use for the credential.
    long-summary: Use with `--keyvault` to create the certificate in Key Vault. Otherwise,
        a certificate will be created locally.
-   name: --keyvault
    short-summary: Name or ID of a KeyVault to use for creating or retrieving certificates.
-   name: --years
    short-summary: 'Number of years for which the credentials will be valid. Default:
        1 year'
-   name: --scopes
    short-summary: >
        Space-separated list of scopes the service principal's role assignment applies
        to.
        Defaults to the root of the current subscription.
-   name: --role
    short-summary: Role of the service principal.
examples:
-   name: Create with a default role assignment.
    text: >
        az ad sp create-for-rbac
-   name: Create using a custom name, and with a default assignment.
    text: >
        az ad sp create-for-rbac -n "MyApp"
-   name: Create without a default assignment.
    text: >
        az ad sp create-for-rbac --skip-assignment
-   name: Create with customized contributor assignments.
    text: |
        az ad sp create-for-rbac -n "MyApp" --role contributor     --scopes /subscriptions/{SubID}/resourceGroups/{ResourceGroup1}     /subscriptions/{SubID}/resourceGroups/{ResourceGroup2}
-   name: Create using a self-signed certificte.
    text: az ad sp create-for-rbac --create-cert
-   name: Create using a self-signed certificate, and store it within KeyVault.
    text: az ad sp create-for-rbac --keyvault MyVault --cert CertName --create-cert
-   name: Create using existing certificate in KeyVault.
    text: az ad sp create-for-rbac --keyvault MyVault --cert CertName
-   name: Create a service principal and configure its access to Azure resources.
    text: az ad sp create-for-rbac --role {role} --scopes {scopes}
    crafted: 'True'
"""

helps["ad sp credential"] = """
type: group
short-summary: manage a service principal's credentials.
long-summary: the credential update will be applied on the Application object the
    service principal is associated with. In other words, you can accomplish the same
    thing using "az ad app credential"
"""

helps["ad sp credential delete"] = """
type: command
short-summary: delete a service principal's credential.
"""

helps["ad sp credential list"] = """
type: command
short-summary: list a service principal's credentials.
examples:
-   name: List a service principal's credentials.
    text: az ad sp credential list --id {id}
    crafted: 'True'
"""

helps["ad sp credential reset"] = """
type: command
short-summary: Reset a service principal credential.
long-summary: Use upon expiration of the service principal's credentials, or in the
    event that login credentials are lost.
parameters:
-   name: --name -n
    short-summary: Name or app URI for the credential.
-   name: --password -p
    short-summary: The password used to log in.
    long-summary: If not present and `--cert` is not specified, a random password
        will be generated.
-   name: --cert
    short-summary: Certificate to use for credentials.
    long-summary: When using `--keyvault,` indicates the name of the cert to use or
        create. Otherwise, supply a PEM or DER formatted public certificate string.
        Use `@{path}` to load from a file. Do not include private key info.
-   name: --create-cert
    short-summary: Create a self-signed certificate to use for the credential.
    long-summary: Use with `--keyvault` to create the certificate in Key Vault. Otherwise,
        a certificate will be created locally.
-   name: --keyvault
    short-summary: Name or ID of a KeyVault to use for creating or retrieving certificates.
-   name: --years
    short-summary: 'Number of years for which the credentials will be valid. Default:
        1 year'
examples:
-   name: Reset a service principal credential.
    text: az ad sp credential reset --name MyAppURIForCredential
    crafted: 'True'
"""

helps["ad sp delete"] = """
type: command
short-summary: Delete a service principal and its role assignments.
examples:
-   name: Delete a service principal and its role assignments.
    text: az ad sp delete --id {id}
    crafted: 'True'
"""

helps["ad sp list"] = """
type: command
short-summary: List service principals.
long-summary: For low latency, by default, only the first 100 will be returned unless
    you provide filter arguments or use "--all"
"""

helps["ad sp owner"] = """
type: group
short-summary: Manage service principal owners.
"""

helps["ad sp owner list"] = """
type: command
short-summary: List service principal owners.
"""

helps["ad sp show"] = """
type: command
short-summary: Get the details of a service principal.
examples:
-   name: Get the details of a service principal.
    text: az ad sp show --id {id}
    crafted: 'True'
"""

helps["ad user"] = """
type: group
short-summary: Manage Azure Active Directory users and user authentication.
examples:
-   name: Request parameters for creating a new work or school account user.
    text: az ad user create --output json --password {password} --user-principal-name
        MyUserPrincipal --display-name MyDisplay
    crafted: 'True'
-   name: Gets user information from the directory.
    text: az ad user show --upn-or-object-id {upn-or-object-id}
    crafted: 'True'
-   name: Delete a user.
    text: az ad user delete --upn-or-object-id {upn-or-object-id}
    crafted: 'True'
"""

helps["ad user get-member-groups"] = """
type: command
short-summary: Get groups of which the user is a member
examples:
-   name: Get groups of which the user is a member.
    text: az ad user get-member-groups --upn-or-object-id {upn-or-object-id}
    crafted: 'True'
"""

helps["ad user list"] = """
type: command
short-summary: List Azure Active Directory users.
examples:
-   name: List Azure Active Directory users.
    text: az ad user list --filter {filter}
    crafted: 'True'
"""

helps["role"] = """
type: group
short-summary: Manage user roles for access control with Azure Active Directory and
    service principals.
"""

helps["role assignment"] = """
type: group
short-summary: Manage role assignments.
"""

helps["role assignment create"] = """
type: command
short-summary: Create a new role assignment for a user, group, or service principal.
examples:
-   name: Create role assignment for an assignee.
    text: az role assignment create --assignee sp_name --role a_role
-   name: Create a new role assignment for a user, group, or service principal.
    text: az role assignment create --role a_role --scope {scope} --assignee sp_name
    crafted: 'True'
"""

helps["role assignment delete"] = """
type: command
short-summary: Delete role assignments.
"""

helps["role assignment list"] = """
type: command
short-summary: List role assignments.
long-summary: By default, only assignments scoped to subscription will be displayed.
    To view assignments scoped by resource or group, use `--all`.
"""

helps["role assignment list-changelogs"] = """
type: command
short-summary: List changelogs for role assignments.
"""

helps["role definition"] = """
type: group
short-summary: Manage role definitions.
"""

helps["role definition create"] = """
type: command
short-summary: Create a custom role definition.
parameters:
-   name: --role-definition
    type: string
    short-summary: Description of a role as JSON, or a path to a file containing a
        JSON description.
examples:
-   name: Create a role with read-only access to storage and network resources, and
        the ability to start or restart VMs.
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
-   name: Create a role from a file containing a JSON description.
    text: >
        az role definition create --role-definition @ad-role.json
-   name: Create a custom role definition.
    text: az role definition create --role-definition @ad-role.json
    crafted: 'True'
"""

helps["role definition delete"] = """
type: command
short-summary: Delete a role definition.
examples:
-   name: Delete a role definition.
    text: az role definition delete --name MyRole
    crafted: 'True'
"""

helps["role definition list"] = """
type: command
short-summary: List role definitions.
"""

helps["role definition update"] = """
type: command
short-summary: Update a role definition.
parameters:
-   name: --role-definition
    type: string
    short-summary: Description of a role as JSON, or a path to a file containing a
        JSON description.
examples:
-   name: Update a role definition.
    text: az role definition update --role-definition {role-definition}
    crafted: 'True'
"""

