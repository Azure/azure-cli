# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PointsFilter(Model):
    """PointsFilter.

    :param configuration_names:
    :type configuration_names: list of str
    :param testcase_ids:
    :type testcase_ids: list of int
    :param testers:
    :type testers: list of :class:`IdentityRef <test.v4_1.models.IdentityRef>`
    """

    _attribute_map = {
        'configuration_names': {'key': 'configurationNames', 'type': '[str]'},
        'testcase_ids': {'key': 'testcaseIds', 'type': '[int]'},
        'testers': {'key': 'testers', 'type': '[IdentityRef]'}
    }

    def __init__(self, configuration_names=None, testcase_ids=None, testers=None):
        super(PointsFilter, self).__init__()
        self.configuration_names = configuration_names
        self.testcase_ids = testcase_ids
        self.testers = testers
