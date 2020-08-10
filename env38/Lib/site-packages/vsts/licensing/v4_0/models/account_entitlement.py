# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountEntitlement(Model):
    """AccountEntitlement.

    :param account_id: Gets or sets the id of the account to which the license belongs
    :type account_id: str
    :param assignment_date: Gets or sets the date the license was assigned
    :type assignment_date: datetime
    :param assignment_source: Assignment Source
    :type assignment_source: object
    :param last_accessed_date: Gets or sets the date of the user last sign-in to this account
    :type last_accessed_date: datetime
    :param license:
    :type license: :class:`License <licensing.v4_0.models.License>`
    :param rights: The computed rights of this user in the account.
    :type rights: :class:`AccountRights <licensing.v4_0.models.AccountRights>`
    :param status: The status of the user in the account
    :type status: object
    :param user: Identity information of the user to which the license belongs
    :type user: :class:`IdentityRef <licensing.v4_0.models.IdentityRef>`
    :param user_id: Gets the id of the user to which the license belongs
    :type user_id: str
    """

    _attribute_map = {
        'account_id': {'key': 'accountId', 'type': 'str'},
        'assignment_date': {'key': 'assignmentDate', 'type': 'iso-8601'},
        'assignment_source': {'key': 'assignmentSource', 'type': 'object'},
        'last_accessed_date': {'key': 'lastAccessedDate', 'type': 'iso-8601'},
        'license': {'key': 'license', 'type': 'License'},
        'rights': {'key': 'rights', 'type': 'AccountRights'},
        'status': {'key': 'status', 'type': 'object'},
        'user': {'key': 'user', 'type': 'IdentityRef'},
        'user_id': {'key': 'userId', 'type': 'str'}
    }

    def __init__(self, account_id=None, assignment_date=None, assignment_source=None, last_accessed_date=None, license=None, rights=None, status=None, user=None, user_id=None):
        super(AccountEntitlement, self).__init__()
        self.account_id = account_id
        self.assignment_date = assignment_date
        self.assignment_source = assignment_source
        self.last_accessed_date = last_accessed_date
        self.license = license
        self.rights = rights
        self.status = status
        self.user = user
        self.user_id = user_id
