# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FailingSince(Model):
    """FailingSince.

    :param build:
    :type build: :class:`BuildReference <test.v4_1.models.BuildReference>`
    :param date:
    :type date: datetime
    :param release:
    :type release: :class:`ReleaseReference <test.v4_1.models.ReleaseReference>`
    """

    _attribute_map = {
        'build': {'key': 'build', 'type': 'BuildReference'},
        'date': {'key': 'date', 'type': 'iso-8601'},
        'release': {'key': 'release', 'type': 'ReleaseReference'}
    }

    def __init__(self, build=None, date=None, release=None):
        super(FailingSince, self).__init__()
        self.build = build
        self.date = date
        self.release = release
