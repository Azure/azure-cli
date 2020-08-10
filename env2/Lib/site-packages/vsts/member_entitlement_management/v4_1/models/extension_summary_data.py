# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .summary_data import SummaryData


class ExtensionSummaryData(SummaryData):
    """ExtensionSummaryData.

    :param assigned: Count of Licenses already assigned.
    :type assigned: int
    :param available: Available Count.
    :type available: int
    :param included_quantity: Quantity
    :type included_quantity: int
    :param total: Total Count.
    :type total: int
    :param assigned_through_subscription: Count of Extension Licenses assigned to users through msdn.
    :type assigned_through_subscription: int
    :param extension_id: Gallery Id of the Extension
    :type extension_id: str
    :param extension_name: Friendly name of this extension
    :type extension_name: str
    :param is_trial_version: Whether its a Trial Version.
    :type is_trial_version: bool
    :param minimum_license_required: Minimum License Required for the Extension.
    :type minimum_license_required: object
    :param remaining_trial_days: Days remaining for the Trial to expire.
    :type remaining_trial_days: int
    :param trial_expiry_date: Date on which the Trial expires.
    :type trial_expiry_date: datetime
    """

    _attribute_map = {
        'assigned': {'key': 'assigned', 'type': 'int'},
        'available': {'key': 'available', 'type': 'int'},
        'included_quantity': {'key': 'includedQuantity', 'type': 'int'},
        'total': {'key': 'total', 'type': 'int'},
        'assigned_through_subscription': {'key': 'assignedThroughSubscription', 'type': 'int'},
        'extension_id': {'key': 'extensionId', 'type': 'str'},
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'is_trial_version': {'key': 'isTrialVersion', 'type': 'bool'},
        'minimum_license_required': {'key': 'minimumLicenseRequired', 'type': 'object'},
        'remaining_trial_days': {'key': 'remainingTrialDays', 'type': 'int'},
        'trial_expiry_date': {'key': 'trialExpiryDate', 'type': 'iso-8601'}
    }

    def __init__(self, assigned=None, available=None, included_quantity=None, total=None, assigned_through_subscription=None, extension_id=None, extension_name=None, is_trial_version=None, minimum_license_required=None, remaining_trial_days=None, trial_expiry_date=None):
        super(ExtensionSummaryData, self).__init__(assigned=assigned, available=available, included_quantity=included_quantity, total=total)
        self.assigned_through_subscription = assigned_through_subscription
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.is_trial_version = is_trial_version
        self.minimum_license_required = minimum_license_required
        self.remaining_trial_days = remaining_trial_days
        self.trial_expiry_date = trial_expiry_date
