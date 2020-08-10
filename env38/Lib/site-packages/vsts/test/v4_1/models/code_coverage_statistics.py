# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CodeCoverageStatistics(Model):
    """CodeCoverageStatistics.

    :param covered: Covered units
    :type covered: int
    :param delta: Delta of coverage
    :type delta: float
    :param is_delta_available: Is delta valid
    :type is_delta_available: bool
    :param label: Label of coverage data ("Blocks", "Statements", "Modules", etc.)
    :type label: str
    :param position: Position of label
    :type position: int
    :param total: Total units
    :type total: int
    """

    _attribute_map = {
        'covered': {'key': 'covered', 'type': 'int'},
        'delta': {'key': 'delta', 'type': 'float'},
        'is_delta_available': {'key': 'isDeltaAvailable', 'type': 'bool'},
        'label': {'key': 'label', 'type': 'str'},
        'position': {'key': 'position', 'type': 'int'},
        'total': {'key': 'total', 'type': 'int'}
    }

    def __init__(self, covered=None, delta=None, is_delta_available=None, label=None, position=None, total=None):
        super(CodeCoverageStatistics, self).__init__()
        self.covered = covered
        self.delta = delta
        self.is_delta_available = is_delta_available
        self.label = label
        self.position = position
        self.total = total
