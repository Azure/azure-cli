# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SubscriptionEvaluationSettings(Model):
    """SubscriptionEvaluationSettings.

    :param enabled: Indicates whether subscription evaluation before saving is enabled or not
    :type enabled: bool
    :param interval: Time interval to check on subscription evaluation job in seconds
    :type interval: int
    :param threshold: Threshold on the number of notifications for considering a subscription too noisy
    :type threshold: int
    :param time_out: Time out for the subscription evaluation check in seconds
    :type time_out: int
    """

    _attribute_map = {
        'enabled': {'key': 'enabled', 'type': 'bool'},
        'interval': {'key': 'interval', 'type': 'int'},
        'threshold': {'key': 'threshold', 'type': 'int'},
        'time_out': {'key': 'timeOut', 'type': 'int'}
    }

    def __init__(self, enabled=None, interval=None, threshold=None, time_out=None):
        super(SubscriptionEvaluationSettings, self).__init__()
        self.enabled = enabled
        self.interval = interval
        self.threshold = threshold
        self.time_out = time_out
