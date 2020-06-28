# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model

class OrganizationDetails(Model):
    _attribute_map = {
        'accountId': {'key': 'accountId', 'type': 'str'},
        'accountHostType': {'key': 'accountHostType', 'type': 'str'},
        'accountName': {'key': 'accountName', 'type': 'str'},
        'subscriptionId': {'key': 'subscriptionId', 'type': 'str'},
        'subscriptionStatus': {'key': 'subscriptionStatus', 'type': 'str'},
        'resourceGroupName': {'key': 'resourceGroupName', 'type': 'str'},
        'geoLocation': {'key': 'geoLocation', 'type': 'str'},
        'locale': {'key': 'locale', 'type': 'str'},
        'regionDisplayName': {'key': 'regionDisplayName', 'type': 'str'},
        'serviceUrls': {'key': 'serviceUrls', 'type': 'str'},
        'accountTenantId': {'key': 'accountTenantId', 'type': 'str'},
        'isAccountOwner': {'key': 'isAccountOwner', 'type': 'str'},
        'resourceName': {'key': 'resourceName', 'type': 'str'},
        'subscriptionName': {'key': 'subscriptionName', 'type': 'str'},
        'isEligibleForPurchase': {'key': 'isEligibleForPurchase', 'type': 'str'},
        'isPrepaidFundSubscription': {'key': 'isPrepaidFundSubscription', 'type': 'str'},
        'isPricingAvailable': {'key': 'isPricingAvailable', 'type': 'str'},
        'subscriptionOfferCode': {'key': 'subscriptionOfferCode', 'type': 'str'},
        'offerType': {'key': 'offerType', 'type': 'str'},
        'subscriptionTenantId': {'key': 'subscriptionTenantId', 'type': 'str'},
        'subscriptionObjectId': {'key': 'subscriptionObjectId', 'type': 'str'},
        'failedPurchaseReason': {'key': 'failedPurchaseReason', 'type': 'str'}
    }

    def __init__(self
                , accountId=None
                , accountHostType=None
                , accountName=None
                , subscriptionId=None
                , subscriptionStatus=None
                , resourceGroupName=None
                , geoLocation=None
                , locale=None
                , regionDisplayName=None
                , serviceUrls=None
                , accountTenantId=None
                , isAccountOwner=None
                , resourceName=None
                , subscriptionName=None
                , isEligibleForPurchase=None
                , isPrepaidFundSubscription=None
                , isPricingAvailable=None
                , subscriptionOfferCode=None
                , offerType=None
                , subscriptionTenantId=None
                , subscriptionObjectId=None
                , failedPurchaseReason=None):
        self.accountId = accountId
        self.accountHostType = accountHostType
        self.accountName = accountName
        self.subscriptionId = subscriptionId
        self.subscriptionStatus = subscriptionStatus
        self.resourceGroupName = resourceGroupName
        self.geoLocation = geoLocation
        self.locale = locale
        self.regionDisplayName = regionDisplayName
        self.serviceUrls = serviceUrls
        self.accountTenantId = accountTenantId
        self.isAccountOwner = isAccountOwner
        self.resourceName = resourceName
        self.subscriptionName = subscriptionName
        self.isEligibleForPurchase = isEligibleForPurchase
        self.isPrepaidFundSubscription = isPrepaidFundSubscription
        self.isPricingAvailable = isPricingAvailable
        self.subscriptionOfferCode = subscriptionOfferCode
        self.offerType = offerType
        self.subscriptionTenantId = subscriptionTenantId
        self.subscriptionObjectId = subscriptionObjectId
        self.failedPurchaseReason = failedPurchaseReason
