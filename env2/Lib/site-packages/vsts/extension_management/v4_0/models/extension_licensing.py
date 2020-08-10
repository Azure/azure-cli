# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionLicensing(Model):
    """ExtensionLicensing.

    :param overrides: A list of contributions which deviate from the default licensing behavior
    :type overrides: list of :class:`LicensingOverride <extension-management.v4_0.models.LicensingOverride>`
    """

    _attribute_map = {
        'overrides': {'key': 'overrides', 'type': '[LicensingOverride]'}
    }

    def __init__(self, overrides=None):
        super(ExtensionLicensing, self).__init__()
        self.overrides = overrides
