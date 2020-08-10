# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProvisioningResult(Model):
    """ProvisioningResult.

    :param provisioning_import_events:
    :type provisioning_import_events: list of str
    """

    _attribute_map = {
        'provisioning_import_events': {'key': 'provisioningImportEvents', 'type': '[str]'}
    }

    def __init__(self, provisioning_import_events=None):
        super(ProvisioningResult, self).__init__()
        self.provisioning_import_events = provisioning_import_events
