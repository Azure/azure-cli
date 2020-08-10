# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitImportTfvcSource(Model):
    """GitImportTfvcSource.

    :param import_history: Set true to import History, false otherwise
    :type import_history: bool
    :param import_history_duration_in_days: Get history for last n days (max allowed value is 180 days)
    :type import_history_duration_in_days: int
    :param path: Path which we want to import (this can be copied from Path Control in Explorer)
    :type path: str
    """

    _attribute_map = {
        'import_history': {'key': 'importHistory', 'type': 'bool'},
        'import_history_duration_in_days': {'key': 'importHistoryDurationInDays', 'type': 'int'},
        'path': {'key': 'path', 'type': 'str'}
    }

    def __init__(self, import_history=None, import_history_duration_in_days=None, path=None):
        super(GitImportTfvcSource, self).__init__()
        self.import_history = import_history
        self.import_history_duration_in_days = import_history_duration_in_days
        self.path = path
