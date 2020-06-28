# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccessLevel(Model):
    """AccessLevel.

    :param account_license_type: Type of Account License (e.g. Express, Stakeholder etc.)
    :type account_license_type: object
    :param assignment_source: Assignment Source of the License (e.g. Group, Unknown etc.
    :type assignment_source: object
    :param license_display_name: Display name of the License
    :type license_display_name: str
    :param licensing_source: Licensing Source (e.g. Account. MSDN etc.)
    :type licensing_source: object
    :param msdn_license_type: Type of MSDN License (e.g. Visual Studio Professional, Visual Studio Enterprise etc.)
    :type msdn_license_type: object
    :param status: User status in the account
    :type status: object
    :param status_message: Status message.
    :type status_message: str
    """

    _attribute_map = {
        'account_license_type': {'key': 'accountLicenseType', 'type': 'object'},
        'assignment_source': {'key': 'assignmentSource', 'type': 'object'},
        'license_display_name': {'key': 'licenseDisplayName', 'type': 'str'},
        'licensing_source': {'key': 'licensingSource', 'type': 'object'},
        'msdn_license_type': {'key': 'msdnLicenseType', 'type': 'object'},
        'status': {'key': 'status', 'type': 'object'},
        'status_message': {'key': 'statusMessage', 'type': 'str'}
    }

    def __init__(self, account_license_type=None, assignment_source=None, license_display_name=None, licensing_source=None, msdn_license_type=None, status=None, status_message=None):
        super(AccessLevel, self).__init__()
        self.account_license_type = account_license_type
        self.assignment_source = assignment_source
        self.license_display_name = license_display_name
        self.licensing_source = licensing_source
        self.msdn_license_type = msdn_license_type
        self.status = status
        self.status_message = status_message
