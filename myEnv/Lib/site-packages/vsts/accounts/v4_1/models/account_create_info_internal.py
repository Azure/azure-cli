# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountCreateInfoInternal(Model):
    """AccountCreateInfoInternal.

    :param account_name:
    :type account_name: str
    :param creator:
    :type creator: str
    :param organization:
    :type organization: str
    :param preferences:
    :type preferences: :class:`AccountPreferencesInternal <accounts.v4_1.models.AccountPreferencesInternal>`
    :param properties:
    :type properties: :class:`object <accounts.v4_1.models.object>`
    :param service_definitions:
    :type service_definitions: list of { key: str; value: str }
    """

    _attribute_map = {
        'account_name': {'key': 'accountName', 'type': 'str'},
        'creator': {'key': 'creator', 'type': 'str'},
        'organization': {'key': 'organization', 'type': 'str'},
        'preferences': {'key': 'preferences', 'type': 'AccountPreferencesInternal'},
        'properties': {'key': 'properties', 'type': 'object'},
        'service_definitions': {'key': 'serviceDefinitions', 'type': '[{ key: str; value: str }]'}
    }

    def __init__(self, account_name=None, creator=None, organization=None, preferences=None, properties=None, service_definitions=None):
        super(AccountCreateInfoInternal, self).__init__()
        self.account_name = account_name
        self.creator = creator
        self.organization = organization
        self.preferences = preferences
        self.properties = properties
        self.service_definitions = service_definitions
