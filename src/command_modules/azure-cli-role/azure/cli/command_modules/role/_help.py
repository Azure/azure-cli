# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["role definition list"] = """
"type": |-
    command
"short-summary": |-
    List role definitions.
"""

helps["ad group owner remove"] = """
"type": |-
    command
"short-summary": |-
    remove a group owner.
"""

helps["role definition delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a role definition.
"examples":
-   "name": |-
        Delete a role definition.
    "text": |-
        az role definition delete --name MyRole
"""

helps["ad group create"] = """
"type": |-
    command
"short-summary": |-
    Create a group in the directory.
"examples":
-   "name": |-
        Create a group in the directory.
    "text": |-
        az ad group create --mail-nickname <mail-nickname> --display-name MyDisplay
"""

helps["role assignment"] = """
"type": |-
    group
"short-summary": |-
    Manage role assignments.
"""

helps["ad sp delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a service principal and its role assignments.
"examples":
-   "name": |-
        Delete a service principal and its role assignments.
    "text": |-
        az ad sp delete --id <id>
"""

helps["role"] = """
"type": |-
    group
"short-summary": |-
    Manage user roles for access control with Azure Active Directory and service principals.
"""

helps["ad sp credential list"] = """
"type": |-
    command
"short-summary": |-
    list a service principal's credentials.
"examples":
-   "name": |-
        List a service principal's credentials.
    "text": |-
        az ad sp credential list --id <id>
"""

helps["ad group member"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Active Directory group members.
"""

helps["ad app owner remove"] = """
"type": |-
    command
"short-summary": |-
    remove an application owner.
"""

helps["ad sp"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Active Directory service principals for automation authentication.
"""

helps["ad app"] = """
"type": |-
    group
"short-summary": |-
    Manage applications with AAD Graph.
"""

helps["ad sp create-for-rbac"] = """
"type": |-
    command
"short-summary": |-
    Create a service principal and configure its access to Azure resources.
"parameters":
-   "name": |-
        --name -n
    "short-summary": |-
        a URI to use as the logic name. It doesn't need to exist. If not present, CLI will generate one.
-   "name": |-
        --password -p
    "short-summary": |-
        The password used to log in.
    "long-summary": |-
        If not present and `--cert` is not specified, a random password will be generated.
-   "name": |-
        --cert
    "short-summary": |-
        Certificate to use for credentials.
    "long-summary": |-
        When used with `--keyvault,` indicates the name of the cert to use or create. Otherwise, supply a PEM or DER formatted public certificate string. Use `@{path}` to load from a file. Do not include private key info.
-   "name": |-
        --create-cert
    "short-summary": |-
        Create a self-signed certificate to use for the credential.
    "long-summary": |-
        Use with `--keyvault` to create the certificate in Key Vault. Otherwise, a certificate will be created locally.
-   "name": |-
        --keyvault
    "short-summary": |-
        Name or ID of a KeyVault to use for creating or retrieving certificates.
-   "name": |-
        --years
    "short-summary": |-
        Number of years for which the credentials will be valid. Default: 1 year
-   "name": |-
        --scopes
    "short-summary": |
        Space-separated list of scopes the service principal's role assignment applies to. Defaults to the root of the current subscription.
-   "name": |-
        --role
    "short-summary": |-
        Role of the service principal.
"""

helps["ad app owner"] = """
"type": |-
    group
"short-summary": |-
    Manage application owners.
"""

helps["ad app permission list"] = """
"type": |-
    command
"short-summary": |-
    List API permissions the application has requested
"""

helps["ad app permission add"] = """
"type": |-
    command
"short-summary": |-
    add an API permission
"long-summary": |-
    invoking "az ad app permission grant" is needed to activate it
"""

helps["ad sp credential reset"] = """
"type": |-
    command
"short-summary": |-
    Reset a service principal credential.
"long-summary": |-
    Use upon expiration of the service principal's credentials, or in the event that login credentials are lost.
"parameters":
-   "name": |-
        --name -n
    "short-summary": |-
        Name or app URI for the credential.
-   "name": |-
        --password -p
    "short-summary": |-
        The password used to log in.
    "long-summary": |-
        If not present and `--cert` is not specified, a random password will be generated.
-   "name": |-
        --cert
    "short-summary": |-
        Certificate to use for credentials.
    "long-summary": |-
        When using `--keyvault,` indicates the name of the cert to use or create. Otherwise, supply a PEM or DER formatted public certificate string. Use `@{path}` to load from a file. Do not include private key info.
-   "name": |-
        --create-cert
    "short-summary": |-
        Create a self-signed certificate to use for the credential.
    "long-summary": |-
        Use with `--keyvault` to create the certificate in Key Vault. Otherwise, a certificate will be created locally.
-   "name": |-
        --keyvault
    "short-summary": |-
        Name or ID of a KeyVault to use for creating or retrieving certificates.
-   "name": |-
        --years
    "short-summary": |-
        Number of years for which the credentials will be valid. Default: 1 year
"examples":
-   "name": |-
        Reset a service principal credential.
    "text": |-
        az ad sp credential reset --name MyAppURIForCredential
"""

helps["role definition update"] = """
"type": |-
    command
"short-summary": |-
    Update a role definition.
"parameters":
-   "name": |-
        --role-definition
    "type": |-
        string
    "short-summary": |-
        Description of a role as JSON, or a path to a file containing a JSON description.
"examples":
-   "name": |-
        Update a role definition.
    "text": |-
        az role definition update --role-definition <role-definition>
"""

helps["ad app update"] = """
"type": |-
    command
"short-summary": |-
    Update an application.
"examples":
-   "name": |-
        Update an application.
    "text": |-
        az ad app update --set groupMembershipClaims=All --id e042ec79-34cd-498f-9d9f-123456781234
"""

helps["ad sp list"] = """
"type": |-
    command
"short-summary": |-
    List service principals.
"long-summary": |-
    For low latency, by default, only the first 100 will be returned unless you provide filter arguments or use "--all"
"""

helps["ad signed-in-user list-owned-objects"] = """
"type": |-
    command
"short-summary": |-
    Get the list of directory objects that are owned by the user
"""

helps["ad app permission grant"] = """
"type": |-
    command
"short-summary": |-
    Grant the app an API permission
"""

helps["ad sp owner"] = """
"type": |-
    group
"short-summary": |-
    Manage service principal owners.
"""

helps["ad app permission"] = """
"type": |-
    group
"short-summary": |-
    manage an application's OAuth2 permissions.
"""

helps["ad app create"] = """
"type": |-
    command
"short-summary": |-
    Create a web application, web API or native application
"examples":
-   "name": |-
        Create a web application, web API or native application.
    "text": |-
        az ad app create --identifier-uris <identifier-uris> --output json --password <password> --display-name MyDisplay
"""

helps["role definition create"] = """
"type": |-
    command
"short-summary": |-
    Create a custom role definition.
"parameters":
-   "name": |-
        --role-definition
    "type": |-
        string
    "short-summary": |-
        Description of a role as JSON, or a path to a file containing a JSON description.
"examples":
-   "name": |-
        Create a custom role definition.
    "text": |-
        az role definition create --role-definition @ad-role.json
"""

helps["ad sp owner list"] = """
"type": |-
    command
"short-summary": |-
    List service principal owners.
"""

helps["ad sp credential delete"] = """
"type": |-
    command
"short-summary": |-
    delete a service principal's credential.
"""

helps["ad group member check"] = """
"type": |-
    command
"short-summary": |-
    Check if a member is in a group.
"examples":
-   "name": |-
        Check if a member is in a group.
    "text": |-
        az ad group member check --group <group> --member-id <member-id>
"""

helps["ad app owner list"] = """
"type": |-
    command
"short-summary": |-
    List application owners.
"examples":
-   "name": |-
        List application owners.
    "text": |-
        az ad app owner list --id <id>
"""

helps["ad signed-in-user"] = """
"type": |-
    group
"short-summary": |-
    Show graph information about current signed-in user in CLI
"""

helps["role definition"] = """
"type": |-
    group
"short-summary": |-
    Manage role definitions.
"""

helps["ad sp create"] = """
"type": |-
    command
"short-summary": |-
    Create a service principal.
"examples":
-   "name": |-
        Create a service principal.
    "text": |-
        az ad sp create --id <id>
-   "name": |-
        Create a service principal and configure its access to Azure resources.
    "text": |-
        az ad sp create-for-rbac --role <role> --scopes <scopes>
"""

helps["ad sp credential"] = """
"type": |-
    group
"short-summary": |-
    manage a service principal's credentials.
"long-summary": |-
    the credential update will be applied on the Application object the service principal is associated with. In other words, you can accomplish the same thing using "az ad app credential"
"""

helps["ad app credential delete"] = """
"type": |-
    command
"short-summary": |-
    delete an application's password or certificate credentials
"""

helps["ad group owner list"] = """
"type": |-
    command
"short-summary": |-
    List group owners.
"""

helps["role assignment delete"] = """
"type": |-
    command
"short-summary": |-
    Delete role assignments.
"""

helps["ad app delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an application.
"examples":
-   "name": |-
        Delete an application.
    "text": |-
        az ad app delete --id <id>
"""

helps["ad group owner add"] = """
"type": |-
    command
"short-summary": |-
    add a group owner.
"""

helps["ad app permission delete"] = """
"type": |-
    command
"short-summary": |-
    remove an API permission
"""

helps["ad group"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Active Directory groups.
"""

helps["ad app show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an application.
"examples":
-   "name": |-
        Get the details of an application.
    "text": |-
        az ad app show --id <id>
"""

helps["ad app list"] = """
"type": |-
    command
"short-summary": |-
    List applications.
"long-summary": |-
    for low latency, by default, only the first 100 will be returned unless you provide filter arguments or use "--all"
"examples":
-   "name": |-
        List applications.
    "text": |-
        az ad app list --output json --query [0]
"""

helps["ad app owner add"] = """
"type": |-
    command
"short-summary": |-
    add an application owner.
"""

helps["role assignment create"] = """
"type": |-
    command
"short-summary": |-
    Create a new role assignment for a user, group, or service principal.
"examples":
-   "name": |-
        Create a new role assignment for a user, group, or service principal.
    "text": |-
        az role assignment create --role a_role --scope <scope> --assignee sp_name
"""

helps["ad app credential list"] = """
"type": |-
    command
"short-summary": |-
    list an application's password or certificate credentials
"""

helps["ad app credential reset"] = """
"type": |-
    command
"short-summary": |-
    append or overwrite an application's password or certificate credentials
"""

helps["ad user"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Active Directory users and user authentication.
"examples":
-   "name": |-
        Get groups of which the user is a member.
    "text": |-
        az ad user get-member-groups --upn-or-object-id <upn-or-object-id>
"""

helps["ad app credential"] = """
"type": |-
    group
"short-summary": |-
    manage an application's password or certificate credentials
"""

helps["ad user get-member-groups"] = """
"type": |-
    command
"short-summary": |-
    Get groups of which the user is a member
"""

helps["ad sp show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a service principal.
"examples":
-   "name": |-
        Get the details of a service principal.
    "text": |-
        az ad sp show --id <id>
"""

helps["ad group owner"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Active Directory group owners.
"""

helps["role assignment list"] = """
"type": |-
    command
"short-summary": |-
    List role assignments.
"long-summary": |-
    By default, only assignments scoped to subscription will be displayed. To view assignments scoped by resource or group, use `--all`.
"""

helps["ad user list"] = """
"type": |-
    command
"short-summary": |-
    List Azure Active Directory users.
"examples":
-   "name": |-
        List Azure Active Directory users.
    "text": |-
        az ad user list --filter <filter>
"""

helps["ad"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Active Directory Graph entities needed for Role Based Access Control
"""

helps["role assignment list-changelogs"] = """
"type": |-
    command
"short-summary": |-
    List changelogs for role assignments.
"""

