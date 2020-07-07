# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RemoteProfile(Model):
    """RemoteProfile.

    :param avatar:
    :type avatar: str
    :param country_code:
    :type country_code: str
    :param display_name:
    :type display_name: str
    :param email_address: Primary contact email from from MSA/AAD
    :type email_address: str
    """

    _attribute_map = {
        'avatar': {'key': 'avatar', 'type': 'str'},
        'country_code': {'key': 'countryCode', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'email_address': {'key': 'emailAddress', 'type': 'str'}
    }

    def __init__(self, avatar=None, country_code=None, display_name=None, email_address=None):
        super(RemoteProfile, self).__init__()
        self.avatar = avatar
        self.country_code = country_code
        self.display_name = display_name
        self.email_address = email_address
