# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskHubLicenseDetails(Model):
    """TaskHubLicenseDetails.

    :param enterprise_users_count:
    :type enterprise_users_count: int
    :param free_hosted_license_count:
    :type free_hosted_license_count: int
    :param free_license_count:
    :type free_license_count: int
    :param has_license_count_ever_updated:
    :type has_license_count_ever_updated: bool
    :param hosted_agent_minutes_free_count:
    :type hosted_agent_minutes_free_count: int
    :param hosted_agent_minutes_used_count:
    :type hosted_agent_minutes_used_count: int
    :param msdn_users_count:
    :type msdn_users_count: int
    :param purchased_hosted_license_count:
    :type purchased_hosted_license_count: int
    :param purchased_license_count:
    :type purchased_license_count: int
    :param total_license_count:
    :type total_license_count: int
    """

    _attribute_map = {
        'enterprise_users_count': {'key': 'enterpriseUsersCount', 'type': 'int'},
        'free_hosted_license_count': {'key': 'freeHostedLicenseCount', 'type': 'int'},
        'free_license_count': {'key': 'freeLicenseCount', 'type': 'int'},
        'has_license_count_ever_updated': {'key': 'hasLicenseCountEverUpdated', 'type': 'bool'},
        'hosted_agent_minutes_free_count': {'key': 'hostedAgentMinutesFreeCount', 'type': 'int'},
        'hosted_agent_minutes_used_count': {'key': 'hostedAgentMinutesUsedCount', 'type': 'int'},
        'msdn_users_count': {'key': 'msdnUsersCount', 'type': 'int'},
        'purchased_hosted_license_count': {'key': 'purchasedHostedLicenseCount', 'type': 'int'},
        'purchased_license_count': {'key': 'purchasedLicenseCount', 'type': 'int'},
        'total_license_count': {'key': 'totalLicenseCount', 'type': 'int'}
    }

    def __init__(self, enterprise_users_count=None, free_hosted_license_count=None, free_license_count=None, has_license_count_ever_updated=None, hosted_agent_minutes_free_count=None, hosted_agent_minutes_used_count=None, msdn_users_count=None, purchased_hosted_license_count=None, purchased_license_count=None, total_license_count=None):
        super(TaskHubLicenseDetails, self).__init__()
        self.enterprise_users_count = enterprise_users_count
        self.free_hosted_license_count = free_hosted_license_count
        self.free_license_count = free_license_count
        self.has_license_count_ever_updated = has_license_count_ever_updated
        self.hosted_agent_minutes_free_count = hosted_agent_minutes_free_count
        self.hosted_agent_minutes_used_count = hosted_agent_minutes_used_count
        self.msdn_users_count = msdn_users_count
        self.purchased_hosted_license_count = purchased_hosted_license_count
        self.purchased_license_count = purchased_license_count
        self.total_license_count = total_license_count
