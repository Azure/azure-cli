# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .summary_data import SummaryData


class LicenseSummaryData(SummaryData):
    """LicenseSummaryData.

    :param assigned: Count of Licenses already assigned.
    :type assigned: int
    :param available: Available Count.
    :type available: int
    :param included_quantity: Quantity
    :type included_quantity: int
    :param total: Total Count.
    :type total: int
    :param account_license_type: Type of Account License.
    :type account_license_type: object
    :param disabled: Count of Disabled Licenses.
    :type disabled: int
    :param is_purchasable: Designates if this license quantity can be changed through purchase
    :type is_purchasable: bool
    :param license_name: Name of the License.
    :type license_name: str
    :param msdn_license_type: Type of MSDN License.
    :type msdn_license_type: object
    :param next_billing_date: Specifies the date when billing will charge for paid licenses
    :type next_billing_date: datetime
    :param source: Source of the License.
    :type source: object
    :param total_after_next_billing_date: Total license count after next billing cycle
    :type total_after_next_billing_date: int
    """

    _attribute_map = {
        'assigned': {'key': 'assigned', 'type': 'int'},
        'available': {'key': 'available', 'type': 'int'},
        'included_quantity': {'key': 'includedQuantity', 'type': 'int'},
        'total': {'key': 'total', 'type': 'int'},
        'account_license_type': {'key': 'accountLicenseType', 'type': 'object'},
        'disabled': {'key': 'disabled', 'type': 'int'},
        'is_purchasable': {'key': 'isPurchasable', 'type': 'bool'},
        'license_name': {'key': 'licenseName', 'type': 'str'},
        'msdn_license_type': {'key': 'msdnLicenseType', 'type': 'object'},
        'next_billing_date': {'key': 'nextBillingDate', 'type': 'iso-8601'},
        'source': {'key': 'source', 'type': 'object'},
        'total_after_next_billing_date': {'key': 'totalAfterNextBillingDate', 'type': 'int'}
    }

    def __init__(self, assigned=None, available=None, included_quantity=None, total=None, account_license_type=None, disabled=None, is_purchasable=None, license_name=None, msdn_license_type=None, next_billing_date=None, source=None, total_after_next_billing_date=None):
        super(LicenseSummaryData, self).__init__(assigned=assigned, available=available, included_quantity=included_quantity, total=total)
        self.account_license_type = account_license_type
        self.disabled = disabled
        self.is_purchasable = is_purchasable
        self.license_name = license_name
        self.msdn_license_type = msdn_license_type
        self.next_billing_date = next_billing_date
        self.source = source
        self.total_after_next_billing_date = total_after_next_billing_date
