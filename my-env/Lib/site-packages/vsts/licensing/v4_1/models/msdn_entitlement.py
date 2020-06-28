# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MsdnEntitlement(Model):
    """MsdnEntitlement.

    :param entitlement_code: Entilement id assigned to Entitlement in Benefits Database.
    :type entitlement_code: str
    :param entitlement_name: Entitlement Name e.g. Downloads, Chat.
    :type entitlement_name: str
    :param entitlement_type: Type of Entitlement e.g. Downloads, Chat.
    :type entitlement_type: str
    :param is_activated: Entitlement activation status
    :type is_activated: bool
    :param is_entitlement_available: Entitlement availability
    :type is_entitlement_available: bool
    :param subscription_channel: Write MSDN Channel into CRCT (Retail,MPN,VL,BizSpark,DreamSpark,MCT,FTE,Technet,WebsiteSpark,Other)
    :type subscription_channel: str
    :param subscription_expiration_date: Subscription Expiration Date.
    :type subscription_expiration_date: datetime
    :param subscription_id: Subscription id which identifies the subscription itself. This is the Benefit Detail Guid from BMS.
    :type subscription_id: str
    :param subscription_level_code: Identifier of the subscription or benefit level.
    :type subscription_level_code: str
    :param subscription_level_name: Name of subscription level.
    :type subscription_level_name: str
    :param subscription_status: Subscription Status Code (ACT, PND, INA ...).
    :type subscription_status: str
    """

    _attribute_map = {
        'entitlement_code': {'key': 'entitlementCode', 'type': 'str'},
        'entitlement_name': {'key': 'entitlementName', 'type': 'str'},
        'entitlement_type': {'key': 'entitlementType', 'type': 'str'},
        'is_activated': {'key': 'isActivated', 'type': 'bool'},
        'is_entitlement_available': {'key': 'isEntitlementAvailable', 'type': 'bool'},
        'subscription_channel': {'key': 'subscriptionChannel', 'type': 'str'},
        'subscription_expiration_date': {'key': 'subscriptionExpirationDate', 'type': 'iso-8601'},
        'subscription_id': {'key': 'subscriptionId', 'type': 'str'},
        'subscription_level_code': {'key': 'subscriptionLevelCode', 'type': 'str'},
        'subscription_level_name': {'key': 'subscriptionLevelName', 'type': 'str'},
        'subscription_status': {'key': 'subscriptionStatus', 'type': 'str'}
    }

    def __init__(self, entitlement_code=None, entitlement_name=None, entitlement_type=None, is_activated=None, is_entitlement_available=None, subscription_channel=None, subscription_expiration_date=None, subscription_id=None, subscription_level_code=None, subscription_level_name=None, subscription_status=None):
        super(MsdnEntitlement, self).__init__()
        self.entitlement_code = entitlement_code
        self.entitlement_name = entitlement_name
        self.entitlement_type = entitlement_type
        self.is_activated = is_activated
        self.is_entitlement_available = is_entitlement_available
        self.subscription_channel = subscription_channel
        self.subscription_expiration_date = subscription_expiration_date
        self.subscription_id = subscription_id
        self.subscription_level_code = subscription_level_code
        self.subscription_level_name = subscription_level_name
        self.subscription_status = subscription_status
