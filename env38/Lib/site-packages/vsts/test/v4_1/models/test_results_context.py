# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultsContext(Model):
    """TestResultsContext.

    :param build:
    :type build: :class:`BuildReference <test.v4_1.models.BuildReference>`
    :param context_type:
    :type context_type: object
    :param release:
    :type release: :class:`ReleaseReference <test.v4_1.models.ReleaseReference>`
    """

    _attribute_map = {
        'build': {'key': 'build', 'type': 'BuildReference'},
        'context_type': {'key': 'contextType', 'type': 'object'},
        'release': {'key': 'release', 'type': 'ReleaseReference'}
    }

    def __init__(self, build=None, context_type=None, release=None):
        super(TestResultsContext, self).__init__()
        self.build = build
        self.context_type = context_type
        self.release = release
