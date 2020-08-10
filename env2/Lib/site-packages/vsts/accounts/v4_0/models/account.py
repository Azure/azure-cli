# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Account(Model):
    """Account.

    :param account_id: Identifier for an Account
    :type account_id: str
    :param account_name: Name for an account
    :type account_name: str
    :param account_owner: Owner of account
    :type account_owner: str
    :param account_status: Current account status
    :type account_status: object
    :param account_type: Type of account: Personal, Organization
    :type account_type: object
    :param account_uri: Uri for an account
    :type account_uri: str
    :param created_by: Who created the account
    :type created_by: str
    :param created_date: Date account was created
    :type created_date: datetime
    :param has_moved:
    :type has_moved: bool
    :param last_updated_by: Identity of last person to update the account
    :type last_updated_by: str
    :param last_updated_date: Date account was last updated
    :type last_updated_date: datetime
    :param namespace_id: Namespace for an account
    :type namespace_id: str
    :param new_collection_id:
    :type new_collection_id: str
    :param organization_name: Organization that created the account
    :type organization_name: str
    :param properties: Extended properties
    :type properties: :class:`object <accounts.v4_0.models.object>`
    :param status_reason: Reason for current status
    :type status_reason: str
    """

    _attribute_map = {
        'account_id': {'key': 'accountId', 'type': 'str'},
        'account_name': {'key': 'accountName', 'type': 'str'},
        'account_owner': {'key': 'accountOwner', 'type': 'str'},
        'account_status': {'key': 'accountStatus', 'type': 'object'},
        'account_type': {'key': 'accountType', 'type': 'object'},
        'account_uri': {'key': 'accountUri', 'type': 'str'},
        'created_by': {'key': 'createdBy', 'type': 'str'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'has_moved': {'key': 'hasMoved', 'type': 'bool'},
        'last_updated_by': {'key': 'lastUpdatedBy', 'type': 'str'},
        'last_updated_date': {'key': 'lastUpdatedDate', 'type': 'iso-8601'},
        'namespace_id': {'key': 'namespaceId', 'type': 'str'},
        'new_collection_id': {'key': 'newCollectionId', 'type': 'str'},
        'organization_name': {'key': 'organizationName', 'type': 'str'},
        'properties': {'key': 'properties', 'type': 'object'},
        'status_reason': {'key': 'statusReason', 'type': 'str'}
    }

    def __init__(self, account_id=None, account_name=None, account_owner=None, account_status=None, account_type=None, account_uri=None, created_by=None, created_date=None, has_moved=None, last_updated_by=None, last_updated_date=None, namespace_id=None, new_collection_id=None, organization_name=None, properties=None, status_reason=None):
        super(Account, self).__init__()
        self.account_id = account_id
        self.account_name = account_name
        self.account_owner = account_owner
        self.account_status = account_status
        self.account_type = account_type
        self.account_uri = account_uri
        self.created_by = created_by
        self.created_date = created_date
        self.has_moved = has_moved
        self.last_updated_by = last_updated_by
        self.last_updated_date = last_updated_date
        self.namespace_id = namespace_id
        self.new_collection_id = new_collection_id
        self.organization_name = organization_name
        self.properties = properties
        self.status_reason = status_reason
