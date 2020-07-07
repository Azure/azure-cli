# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountLicenseExtensionUsage(Model):
    """AccountLicenseExtensionUsage.

    :param extension_id:
    :type extension_id: str
    :param extension_name:
    :type extension_name: str
    :param included_quantity:
    :type included_quantity: int
    :param is_trial:
    :type is_trial: bool
    :param minimum_license_required:
    :type minimum_license_required: object
    :param msdn_used_count:
    :type msdn_used_count: int
    :param provisioned_count:
    :type provisioned_count: int
    :param remaining_trial_days:
    :type remaining_trial_days: int
    :param trial_expiry_date:
    :type trial_expiry_date: datetime
    :param used_count:
    :type used_count: int
    """

    _attribute_map = {
        'extension_id': {'key': 'extensionId', 'type': 'str'},
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'included_quantity': {'key': 'includedQuantity', 'type': 'int'},
        'is_trial': {'key': 'isTrial', 'type': 'bool'},
        'minimum_license_required': {'key': 'minimumLicenseRequired', 'type': 'object'},
        'msdn_used_count': {'key': 'msdnUsedCount', 'type': 'int'},
        'provisioned_count': {'key': 'provisionedCount', 'type': 'int'},
        'remaining_trial_days': {'key': 'remainingTrialDays', 'type': 'int'},
        'trial_expiry_date': {'key': 'trialExpiryDate', 'type': 'iso-8601'},
        'used_count': {'key': 'usedCount', 'type': 'int'}
    }

    def __init__(self, extension_id=None, extension_name=None, included_quantity=None, is_trial=None, minimum_license_required=None, msdn_used_count=None, provisioned_count=None, remaining_trial_days=None, trial_expiry_date=None, used_count=None):
        super(AccountLicenseExtensionUsage, self).__init__()
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.included_quantity = included_quantity
        self.is_trial = is_trial
        self.minimum_license_required = minimum_license_required
        self.msdn_used_count = msdn_used_count
        self.provisioned_count = provisioned_count
        self.remaining_trial_days = remaining_trial_days
        self.trial_expiry_date = trial_expiry_date
        self.used_count = used_count
