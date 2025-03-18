# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

IDENTITY_TYPE_SYSTEM_ASSIGNED = 'systemAssignedIdentity'
IDENTITY_TYPE_USER_ASSIGNED = 'userAssignedIdentity'

ID_TYPE_SYSTEM_ASSIGNED = 'MSI'
ID_TYPE_USER_ASSIGNED_CLIENT_ID = 'MSIClient'
ID_TYPE_USER_ASSIGNED_OBJECT_ID = 'MSIObject'
ID_TYPE_USER_ASSIGNED_RESOURCE_ID = 'MSIResource'


# A managed identity account contains
# "user": {
#     "assignedIdentityInfo": "MSIClient-00000000-0000-0000-0000-000000000000",  # id_string
#     "name": "userAssignedIdentity",  # identity_type
#     "type": "servicePrincipal"
# }

def parse_ids(client_id=None, object_id=None, resource_id=None):
    """Parse IDs into account information:

    - id_string, e.g. MSIObject-00000000-0000-0000-0000-000000000000
    - identity_type, i.e. systemAssignedIdentity/userAssignedIdentity
    """
    # System-assigned - if no ID is provided
    # See https://github.com/Azure/azure-cli/issues/13188
    if not any((client_id, object_id, resource_id)):
        return ID_TYPE_SYSTEM_ASSIGNED, IDENTITY_TYPE_SYSTEM_ASSIGNED

    # User-assigned - if one ID is provided
    id_type = None
    id_value = None
    if client_id:
        id_type = ID_TYPE_USER_ASSIGNED_CLIENT_ID
        id_value = client_id
    elif object_id:
        id_type = ID_TYPE_USER_ASSIGNED_OBJECT_ID
        id_value = object_id
    elif resource_id:
        id_type = ID_TYPE_USER_ASSIGNED_RESOURCE_ID
        id_value = resource_id
    return '{}-{}'.format(id_type, id_value), IDENTITY_TYPE_USER_ASSIGNED

def credential_factory(id_string):
    """Build a ManagedIdentityCredential from id_string."""
    from azure.cli.core.auth.msal_credentials import ManagedIdentityCredential

    id_parts = id_string.split('-', maxsplit=1)

    if id_parts[0] == ID_TYPE_SYSTEM_ASSIGNED:
        return ManagedIdentityCredential()

    id_type, id_value = id_parts
    if id_type == ID_TYPE_USER_ASSIGNED_CLIENT_ID:
        return ManagedIdentityCredential(client_id=id_value)
    if id_type == ID_TYPE_USER_ASSIGNED_OBJECT_ID:
        return ManagedIdentityCredential(object_id=id_value)
    if id_type == ID_TYPE_USER_ASSIGNED_RESOURCE_ID:
        return ManagedIdentityCredential(resource_id=id_value)

    raise ValueError("unrecognized ID type '{}'".format(id_type))
