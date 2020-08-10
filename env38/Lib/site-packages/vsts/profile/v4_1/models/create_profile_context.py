# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CreateProfileContext(Model):
    """CreateProfileContext.

    :param cIData:
    :type cIData: dict
    :param contact_with_offers:
    :type contact_with_offers: bool
    :param country_name:
    :type country_name: str
    :param display_name:
    :type display_name: str
    :param email_address:
    :type email_address: str
    :param has_account:
    :type has_account: bool
    :param language:
    :type language: str
    :param phone_number:
    :type phone_number: str
    :param profile_state:
    :type profile_state: object
    """

    _attribute_map = {
        'cIData': {'key': 'cIData', 'type': '{object}'},
        'contact_with_offers': {'key': 'contactWithOffers', 'type': 'bool'},
        'country_name': {'key': 'countryName', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'email_address': {'key': 'emailAddress', 'type': 'str'},
        'has_account': {'key': 'hasAccount', 'type': 'bool'},
        'language': {'key': 'language', 'type': 'str'},
        'phone_number': {'key': 'phoneNumber', 'type': 'str'},
        'profile_state': {'key': 'profileState', 'type': 'object'}
    }

    def __init__(self, cIData=None, contact_with_offers=None, country_name=None, display_name=None, email_address=None, has_account=None, language=None, phone_number=None, profile_state=None):
        super(CreateProfileContext, self).__init__()
        self.cIData = cIData
        self.contact_with_offers = contact_with_offers
        self.country_name = country_name
        self.display_name = display_name
        self.email_address = email_address
        self.has_account = has_account
        self.language = language
        self.phone_number = phone_number
        self.profile_state = profile_state
