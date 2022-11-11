# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['ad'] = """
type: group
short-summary: Manage Azure Active Directory Graph entities needed for Role Based Access Control
"""

helps['ad app'] = """
type: group
short-summary: Manage applications with AAD Graph.
"""

helps['ad app create'] = """
type: command
short-summary: Create a web application, web API or native application
long-summary: For more detailed documentation, see https://docs.microsoft.com/graph/api/resources/application
examples:
  - name: Create an application.
    text: |
        az ad app create --display-name mytestapp
  - name: Create an application that can fall back to public client with Microsoft Graph delegated permission Application.Read.All
    text: |
        az ad app create --display-name my-public --is-fallback-public-client --required-resource-accesses @manifest.json
        ("manifest.json" contains the following content)
        [{
            "resourceAppId": "00000003-0000-0000-c000-000000000000",
            "resourceAccess": [
                {
                    "id": "c79f8feb-a9db-4090-85f9-90d820caa0eb",
                    "type": "Scope"
                }
           ]
        }]
  - name: Create an application with a role
    text: |
        az ad app create --display-name mytestapp --identifier-uris https://mytestapp.websites.net --app-roles @manifest.json
        ("manifest.json" contains the following content)
        [{
            "allowedMemberTypes": [
              "User"
            ],
            "description": "Approvers can mark documents as approved",
            "displayName": "Approver",
            "isEnabled": "true",
            "value": "approver"
        }]
  - name: Create an application with optional claims
    text: |
        az ad app create --display-name mytestapp --optional-claims @manifest.json
        ("manifest.json" contains the following content)
        {
            "idToken": [
                {
                    "name": "auth_time",
                    "essential": false
                }
            ],
            "accessToken": [
                {
                    "name": "ipaddr",
                    "essential": false
                }
            ],
            "saml2Token": [
                {
                    "name": "upn",
                    "essential": false
                },
                {
                    "name": "extension_ab603c56068041afb2f6832e2a17e237_skypeId",
                    "source": "user",
                    "essential": false
                }
            ]
        }
"""

helps['ad app credential'] = """
type: group
short-summary: Manage an application's password or certificate credentials
"""

helps['ad app credential delete'] = """
type: command
short-summary: Delete an application's password or certificate credentials
examples:
- name: Delete an application's password credentials
  text: az ad app credential delete --id 00000000-0000-0000-0000-000000000000 --key-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- name: Delete an application's certificate credentials
  text: az ad app credential delete --id 00000000-0000-0000-0000-000000000000 --key-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --cert
"""

helps['ad app credential list'] = """
type: command
short-summary: List an application's password or certificate credential metadata. (The content of the password or certificate credential is not retrievable.)
examples:
- name: List an application's password credentials
  text: az ad app credential list --id 00000000-0000-0000-0000-000000000000
- name: List an application's certificate credentials
  text: az ad app credential list --id 00000000-0000-0000-0000-000000000000 --cert
"""

helps['ad app credential reset'] = """
type: command
short-summary: Reset an application's password or certificate credentials
long-summary: >-
    By default, this command clears all passwords and keys, and let graph service generate a password credential.


    The output includes credentials that you must protect. Be sure that you do not include these credentials
    in your code or check the credentials into your source control. As an alternative, consider using
    [managed identities](https://aka.ms/azadsp-managed-identities) if available to avoid the need to use credentials.
examples:
- name: Reset an application's credential with a password
  text: az ad app credential reset --id 00000000-0000-0000-0000-000000000000
- name: Reset an application's credential with a new self-signed certificate
  text: az ad app credential reset --id 00000000-0000-0000-0000-000000000000 --create-cert
- name: Append a certificate to the application with the certificate string.
  text: az ad app credential reset --id 00000000-0000-0000-0000-000000000000 --cert "MIICoT..." --append
- name: Append a certificate to the application with the certificate file.
  text: |-
      az ad app credential reset --id 00000000-0000-0000-0000-000000000000 --cert "@~/cert.pem" --append
      `cert.pem` contains the following content
      -----BEGIN CERTIFICATE-----  <<< this line is optional
      MIICoT...
      -----END CERTIFICATE-----    <<< this line is optional
"""

helps['ad app delete'] = """
type: command
short-summary: Delete an application.
examples:
  - name: Delete an application. (autogenerated)
    text: az ad app delete --id 00000000-0000-0000-0000-000000000000
    crafted: true
"""

helps['ad app list'] = """
type: command
short-summary: List applications.
long-summary: For low latency, by default, only the first 100 will be returned unless you provide filter arguments or use "--all"
"""

helps['ad app owner'] = """
type: group
short-summary: Manage application owners.
"""

helps['ad app owner add'] = """
type: command
short-summary: Add an application owner.
examples:
  - name: add an application owner. (autogenerated)
    text: az ad app owner add --id 00000000-0000-0000-0000-000000000000 --owner-object-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    crafted: true
"""

helps['ad app owner list'] = """
type: command
short-summary: List application owners.
examples:
  - name: List application owners. (autogenerated)
    text: az ad app owner list --id 00000000-0000-0000-0000-000000000000
    crafted: true
"""

helps['ad app owner remove'] = """
type: command
short-summary: Remove an application owner.
"""

helps['ad app permission'] = """
type: group
short-summary: Manage an application's OAuth2 permissions.
"""

helps['ad app permission add'] = """
type: command
short-summary: Add an API permission
long-summary: >-
    Invoking "az ad app permission grant" is needed to activate it.


    To get available permissions of the resource app, run `az ad sp show --id <resource-appId>`. For example,
    to get available permissions for Microsoft Graph API, run `az ad sp show --id 00000003-0000-0000-c000-000000000000`.
    Application permissions under the `appRoles` property correspond to `Role` in --api-permissions.
    Delegated permissions under the `oauth2Permissions` property correspond to `Scope` in --api-permissions.
examples:
  - name: Add Microsoft Graph delegated permission User.Read (Sign in and read user profile).
    text: az ad app permission add --id {appId} --api 00000003-0000-0000-c000-000000000000 --api-permissions e1fe6dd8-ba31-4d61-89e7-88639da4683d=Scope
  - name: Add Microsoft Graph application permission Application.ReadWrite.All (Read and write all applications).
    text: az ad app permission add --id {appId} --api 00000003-0000-0000-c000-000000000000 --api-permissions 1bfefb4e-e0b5-418b-a88f-73c46d2cc8e9=Role
"""

helps['ad app permission admin-consent'] = """
type: command
short-summary: Grant Application & Delegated permissions through admin-consent.
long-summary: You must login as a global administrator
examples:
  - name: Grant Application & Delegated permissions through admin-consent. (autogenerated)
    text: az ad app permission admin-consent --id 00000000-0000-0000-0000-000000000000
    crafted: true
"""

helps['ad app permission delete'] = """
type: command
short-summary: Remove an API permission
examples:
  - name: Remove Azure Active Directory Graph permissions.
    text: az ad app permission delete --id eeba0b46-78e5-4a1a-a1aa-cafe6c123456 --api 00000002-0000-0000-c000-000000000000
  - name: Remove Azure Active Directory Graph delegated permission User.Read (Sign in and read user profile).
    text: az ad app permission delete --id eeba0b46-78e5-4a1a-a1aa-cafe6c123456 --api 00000002-0000-0000-c000-000000000000 --api-permissions 311a71cc-e848-46a1-bdf8-97ff7156d8e6
"""

helps['ad app permission grant'] = """
type: command
short-summary: Grant the app an API Delegated permissions
long-summary: >
    A service principal must exist for the app when running this command. To create a corresponding service
    principal, use `az ad sp create --id {appId}`.

    For Application permissions, please use "ad app permission admin-consent"
examples:
  - name: Grant a native application with permissions to access an existing API with TTL of 2 years
    text: az ad app permission grant --id e042ec79-34cd-498f-9d9f-1234234 --api a0322f79-57df-498f-9d9f-12678 --scope Directory.Read.All
"""

helps['ad app permission list'] = """
type: command
short-summary: List API permissions the application has requested
examples:
  - name: List the OAuth2 permissions for an existing AAD app
    text: az ad app permission list --id e042ec79-34cd-498f-9d9f-1234234
"""

helps['ad app permission list-grants'] = """
type: command
short-summary: List Oauth2 permission grants
examples:
  - name: list oauth2 permissions granted to the service principal
    text: az ad app permission list-grants --id e042ec79-34cd-498f-9d9f-1234234123456
"""

helps['ad app show'] = """
type: command
short-summary: Get the details of an application.
examples:
  - name: Get the details of an application with appId.
    text: az ad app show --id 00000000-0000-0000-0000-000000000000
  - name: Get the details of an application with id.
    text: az ad app show --id 00000000-0000-0000-0000-000000000000
  - name: Get the details of an application with identifier URI.
    text: az ad app show --id api://myapp
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
  - name: declare an application role
    text: |
        az ad app update --id e042ec79-34cd-498f-9d9f-123456781234 --app-roles @manifest.json
        ("manifest.json" contains the following content)
        [{
            "allowedMemberTypes": [
              "User"
            ],
            "description": "Approvers can mark documents as approved",
            "displayName": "Approver",
            "isEnabled": "true",
            "value": "approver"
        }]
  - name: update optional claims
    text: |
        az ad app update --id e042ec79-34cd-498f-9d9f-123456781234 --optional-claims @manifest.json
        ("manifest.json" contains the following content)
        {
            "idToken": [
                {
                    "name": "auth_time",
                    "essential": false
                }
            ],
            "accessToken": [
                {
                    "name": "ipaddr",
                    "essential": false
                }
            ],
            "saml2Token": [
                {
                    "name": "upn",
                    "essential": false
                },
                {
                    "name": "extension_ab603c56068041afb2f6832e2a17e237_skypeId",
                    "source": "user",
                    "essential": false
                }
            ]
        }
  - name: update an application's group membership claims to "All"
    text: >
        az ad app update --id e042ec79-34cd-498f-9d9f-123456781234 --set groupMembershipClaims=All

"""

helps['ad app federated-credential'] = """
type: group
short-summary: Manage application federated identity credentials.
"""

helps['ad app federated-credential list'] = """
type: command
short-summary: List application federated identity credentials.
examples:
- name: List application federated identity credentials.
  text: az ad app federated-credential list --id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
"""

# The example is from
# https://docs.microsoft.com/en-us/azure/active-directory/develop/workload-identity-federation-create-trust-github?tabs=microsoft-graph
helps['ad app federated-credential create'] = """
type: command
short-summary: Create application federated identity credential.
examples:
- name: Create application federated identity credential.
  text: |
    az ad app federated-credential create --id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --parameters credential.json
    ("credential.json" contains the following content)
    {
        "name": "Testing",
        "issuer": "https://token.actions.githubusercontent.com/",
        "subject": "repo:octo-org/octo-repo:environment:Production",
        "description": "Testing",
        "audiences": [
            "api://AzureADTokenExchange"
        ]
    }
"""

helps['ad app federated-credential show'] = """
type: command
short-summary: Show application federated identity credential.
examples:
- name: Show application federated identity credential with id
  text: az ad app federated-credential show --id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --federated-credential-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- name: Show application federated identity credential with name
  text: az ad app federated-credential show --id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --federated-credential-id Testing
"""

helps['ad app federated-credential update'] = """
type: command
short-summary: Update application federated identity credential.
examples:
- name: Update application federated identity credential. Note that 'name' property cannot be changed.
  text: |
    az ad app federated-credential update --id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --federated-credential-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --parameters credential.json
    ("credential.json" contains the following content)
    {
        "issuer": "https://token.actions.githubusercontent.com/",
        "subject": "repo:octo-org/octo-repo:environment:Production",
        "description": "Updated description",
        "audiences": [
            "api://AzureADTokenExchange"
        ]
    }
"""

helps['ad app federated-credential delete'] = """
type: command
short-summary: Delete application federated identity credential.
examples:
- name: Delete application federated identity credential.
  text: az ad app federated-credential delete --id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --federated-credential-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
"""

helps['ad group'] = """
type: group
short-summary: Manage Azure Active Directory groups.
"""

helps['ad group create'] = """
type: command
short-summary: Create a group in the directory.
examples:
  - name: Create a group in the directory. (autogenerated)
    text: az ad group create --display-name MyDisplay --mail-nickname MyDisplay
    crafted: true
"""

helps['ad group member'] = """
type: group
short-summary: Manage Azure Active Directory group members.
"""

helps['ad group member check'] = """
type: command
short-summary: Check if a member is in a group.
examples:
  - name: Check if a member is in a group. (autogenerated)
    text: az ad group member check --group MyGroupDisplayName --member-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    crafted: true
"""

helps['ad group owner'] = """
type: group
short-summary: Manage Azure Active Directory group owners.
"""

helps['ad group owner add'] = """
type: command
short-summary: Add a group owner.
examples:
  - name: add a group owner. (autogenerated)
    text: az ad group owner add --group MyGroupDisplayName --owner-object-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    crafted: true
"""

helps['ad group owner list'] = """
type: command
short-summary: List group owners.
examples:
  - name: List group owners. (autogenerated)
    text: az ad group owner list --group MyGroupDisplayName
    crafted: true
"""

helps['ad group owner remove'] = """
type: command
short-summary: Remove a group owner.
examples:
  - name: remove a group owner. (autogenerated)
    text: az ad group owner remove --group MyGroupDisplayName --owner-object-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    crafted: true
"""

helps['ad signed-in-user'] = """
type: group
short-summary: Show graph information about current signed-in user in CLI
"""

helps['ad signed-in-user list-owned-objects'] = """
type: command
short-summary: Get the list of directory objects that are owned by the user
"""

helps['ad sp'] = """
type: group
short-summary: Manage Azure Active Directory service principals for automation authentication.
"""

helps['ad sp create'] = """
type: command
short-summary: Create a service principal.
examples:
  - name: Create a service principal. (autogenerated)
    text: az ad sp create --id 00000000-0000-0000-0000-000000000000
    crafted: true
"""

helps['ad sp create-for-rbac'] = """
type: command
short-summary: Create a service principal and configure its access to Azure resources.
long-summary: >-
    The output includes credentials that you must protect. Be sure that you do not include these credentials
    in your code or check the credentials into your source control. As an alternative, consider using
    [managed identities](https://aka.ms/azadsp-managed-identities) if available to avoid the need to use credentials.


    By default, this command does not assign any role to the service principal.
    You may use --role and --scopes to assign a specific role and narrow the scope to a resource or resource group.
    You may also use `az role assignment create` to create role assignments for this service principal later.
    See [steps to add a role assignment](https://aka.ms/azadsp-more) for more information.
examples:
  - name: Create without role assignment.
    text: az ad sp create-for-rbac
  - name: Create using a custom display name.
    text: az ad sp create-for-rbac -n MyApp
  - name: Create with a Contributor role assignments on specified scopes. To retrieve current subscription ID, run `az account show --query id --output tsv`.
    text: az ad sp create-for-rbac -n MyApp --role Contributor --scopes /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/resourceGroup1 /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/resourceGroup2
  - name: Create using a self-signed certificate.
    text: az ad sp create-for-rbac --create-cert
  - name: Create using a self-signed certificate, and store it within KeyVault.
    text: az ad sp create-for-rbac --keyvault MyVault --cert CertName --create-cert
  - name: Create using existing certificate in KeyVault.
    text: az ad sp create-for-rbac --keyvault MyVault --cert CertName
"""

helps['ad sp credential'] = """
type: group
short-summary: Manage a service principal's password or certificate credentials
"""

helps['ad sp credential delete'] = """
type: command
short-summary: Delete a service principal's password or certificate credentials
examples:
- name: Delete a service principal's password credential
  text: az ad sp credential delete --id 00000000-0000-0000-0000-000000000000 --key-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- name: Delete a service principal's certificate credential
  text: az ad sp credential delete --id 00000000-0000-0000-0000-000000000000 --key-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --cert
"""

helps['ad sp credential list'] = """
type: command
short-summary: List a service principal's password or certificate credential metadata. (The content of the password or certificate credential is not retrievable.)
examples:
- name: List a service principal's password credentials
  text: az ad sp credential list --id 00000000-0000-0000-0000-000000000000
- name: List a service principal's certificate credentials
  text: az ad sp credential list --id 00000000-0000-0000-0000-000000000000 --cert
"""

helps['ad sp credential reset'] = """
type: command
short-summary: Reset a service principal's password or certificate credentials
long-summary: >-
    By default, this command clears all passwords and keys, and let graph service generate a password credential.


    The output includes credentials that you must protect. Be sure that you do not include these credentials
    in your code or check the credentials into your source control. As an alternative, consider using
    [managed identities](https://aka.ms/azadsp-managed-identities) if available to avoid the need to use credentials.
examples:
- name: Reset a service principal's credential with a password
  text: az ad sp credential reset --id 00000000-0000-0000-0000-000000000000
- name: Reset a service principal's credential with a new self-signed certificate
  text: az ad sp credential reset --id 00000000-0000-0000-0000-000000000000 --create-cert
- name: Append a certificate to the service principal with the certificate string.
  text: az ad sp credential reset --id 00000000-0000-0000-0000-000000000000 --cert "MIICoT..." --append
- name: Append a certificate to the service principal with the certificate file.
  text: |-
      az ad sp credential reset --id 00000000-0000-0000-0000-000000000000 --cert "@~/cert.pem" --append
      `cert.pem` contains the following content
      -----BEGIN CERTIFICATE-----  <<< this line is optional
      MIICoT...
      -----END CERTIFICATE-----    <<< this line is optional
"""

helps['ad sp delete'] = """
type: command
short-summary: Delete a service principal and its role assignments.
examples:
  - name: Delete a service principal and its role assignments. (autogenerated)
    text: az ad sp delete --id 00000000-0000-0000-0000-000000000000
    crafted: true
"""

helps['ad sp list'] = """
type: command
short-summary: List service principals.
long-summary: For low latency, by default, only the first 100 will be returned unless you provide filter arguments or use "--all"
"""

helps['ad sp owner'] = """
type: group
short-summary: Manage service principal owners.
"""

helps['ad sp owner list'] = """
type: command
short-summary: List service principal owners.
examples:
  - name: List service principal owners. (autogenerated)
    text: az ad sp owner list --id 00000000-0000-0000-0000-000000000000
    crafted: true
"""

helps['ad sp show'] = """
type: command
short-summary: Get the details of a service principal.
examples:
  - name: Get the details of a service principal with appId.
    text: az ad sp show --id 00000000-0000-0000-0000-000000000000
  - name: Get the details of a service principal with id.
    text: az ad sp show --id 00000000-0000-0000-0000-000000000000
  - name: Get the details of a service principal with identifier URI.
    text: az ad sp show --id api://myapp
"""

helps['ad sp update'] = """
type: command
short-summary: Update a service principal
examples:
  - name: update a service principal (autogenerated)
    text: az ad sp update --id 00000000-0000-0000-0000-000000000000 --set groupMembershipClaims=All
    crafted: true
"""

helps['ad user'] = """
type: group
short-summary: Manage Azure Active Directory users and user authentication.
"""

helps['ad user create'] = """
type: command
short-summary: Create an Azure Active Directory user.
parameters:
  - name: --force-change-password-next-sign-in
    short-summary: Marks this user as needing to update their password the next time they authenticate. If omitted, false will be used.
  - name: --password
    short-summary: The password that should be assigned to the user for authentication.
examples:
  - name: Create a user
    text: az ad user create --display-name myuser --password password --user-principal-name myuser@contoso.com
"""

helps['ad user get-member-groups'] = """
type: command
short-summary: Get groups of which the user is a member
examples:
  - name: Get groups of which the user is a member
    text: az ad user get-member-groups --id myuser@contoso.com
"""

helps['ad user list'] = """
type: command
short-summary: List Azure Active Directory users.
examples:
  - name: List all the Azure Active Directory users
    text: az ad user list
"""

helps['ad user update'] = """
type: command
short-summary: Update Azure Active Directory users.
examples:
  - name: Update Azure Active Directory users.
    text: az ad user update --id myuser@contoso.com --display-name username2
"""

helps['ad user delete'] = """
type: command
short-summary: Delete Azure Active Directory user.
examples:
  - name: Delete Azure Active Directory users.
    text: az ad user delete --id myuser@contoso.com
"""


helps['ad user show'] = """
type: command
short-summary: Show details for a Azure Active Directory user.
examples:
  - name: Show Azure Active Directory user.
    text: az ad user show --id myuser@contoso.com
"""

helps['ad signed-in-user show'] = """
type: command
short-summary: Get the details for the currently logged-in user.
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
  - name: Create role assignment for an assignee with description and condition.
    text: >-
        az role assignment create --role "Owner" --assignee "John.Doe@Contoso.com"
        --description "Role assignment foo to check on bar"
        --condition "@Resource[Microsoft.Storage/storageAccounts/blobServices/containers:Name] stringEquals 'foo'"
        --condition-version "2.0"
    supported-profiles: latest
  - name: Create a new role assignment for a user, group, or service principal. (autogenerated)
    text: |
        az role assignment create --assignee 00000000-0000-0000-0000-000000000000 --role "Storage Account Key Operator Service Role" --scope $id
    crafted: true
  - name: Create role assignment with your own assignment name.
    text: az role assignment create --assignee-object-id 00000000-0000-0000-0000-000000000000 --assignee-principal-type ServicePrincipal --role Reader --scope /subscriptions/00000000-0000-0000-0000-000000000000 --name 00000000-0000-0000-0000-000000000000
"""


helps['role assignment update'] = """
type: command
short-summary: Update an existing role assignment for a user, group, or service principal.
examples:
  - name: Update a role assignment from a JSON file.
    text: az role assignment update --role-assignment assignment.json
  - name: Update a role assignment from a JSON string. (Bash)
    text: |
        az role assignment update --role-assignment '{
            "canDelegate": null,
            "condition": "@Resource[Microsoft.Storage/storageAccounts/blobServices/containers:Name] stringEquals '"'"'foo'"'"'",
            "conditionVersion": "2.0",
            "description": "Role assignment foo to check on bar",
            "id": "/subscriptions/00000001-0000-0000-0000-000000000000/resourceGroups/rg1/providers/Microsoft.Authorization/roleAssignments/3eabdd43-375b-4dbd-8dc4-04acd15ce56b",
            "name": "3eabdd43-375b-4dbd-8dc4-04acd15ce56b",
            "principalId": "00000002-0000-0000-0000-000000000000",
            "principalType": "User",
            "resourceGroup": "rg1",
            "roleDefinitionId": "/subscriptions/00000001-0000-0000-0000-000000000000/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",
            "scope": "/subscriptions/00000001-0000-0000-0000-000000000000/resourceGroups/rg1",
            "type": "Microsoft.Authorization/roleAssignments"
        }'
"""

helps['role assignment delete'] = """
type: command
short-summary: Delete role assignments.
examples:
  - name: Delete role assignments. (autogenerated)
    text: |
        az role assignment delete --assignee 00000000-0000-0000-0000-000000000000 --role "Storage Account Key Operator Service Role"
    crafted: true
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
  - name: Create a role with read-only access to storage and network resources, and the ability to start or restart VMs. (Bash)
    text: |
        az role definition create --role-definition '{
            "Name": "Contoso On-call",
            "Description": "Perform VM actions and read storage and network information.",
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
examples:
  - name: Delete a role definition. (autogenerated)
    text: az role definition delete --name MyRole
    crafted: true
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
    short-summary: Description of an existing role as JSON, or a path to a file containing a JSON description.
examples:
  - name: Update a role using the output of "az role definition list". (Bash)
    text: |
        az role definition update --role-definition '{
            "roleName": "Contoso On-call",
            "Description": "Perform VM actions and read storage and network information.",
            "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/providers/Microsoft.Authorization/roleDefinitions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "roleType": "CustomRole",
            "type": "Microsoft.Authorization/roleDefinitions",
            "Actions": [
                "Microsoft.Compute/*/read",
                "Microsoft.Compute/virtualMachines/start/action",
                "Microsoft.Compute/virtualMachines/restart/action",
                "Microsoft.Network/*/read",
                "Microsoft.Storage/*/read",
                "Microsoft.Authorization/*/read",
                "Microsoft.Resources/subscriptions/resourceGroups/read",
                "Microsoft.Resources/subscriptions/resourceGroups/resources/read",
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
"""
