# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CoverageStatistics(Model):
    """CoverageStatistics.

    :param blocks_covered:
    :type blocks_covered: int
    :param blocks_not_covered:
    :type blocks_not_covered: int
    :param lines_covered:
    :type lines_covered: int
    :param lines_not_covered:
    :type lines_not_covered: int
    :param lines_partially_covered:
    :type lines_partially_covered: int
    """

    _attribute_map = {
        'blocks_covered': {'key': 'blocksCovered', 'type': 'int'},
        'blocks_not_covered': {'key': 'blocksNotCovered', 'type': 'int'},
        'lines_covered': {'key': 'linesCovered', 'type': 'int'},
        'lines_not_covered': {'key': 'linesNotCovered', 'type': 'int'},
        'lines_partially_covered': {'key': 'linesPartiallyCovered', 'type': 'int'}
    }

    def __init__(self, blocks_covered=None, blocks_not_covered=None, lines_covered=None, lines_not_covered=None, lines_partially_covered=None):
        super(CoverageStatistics, self).__init__()
        self.blocks_covered = blocks_covered
        self.blocks_not_covered = blocks_not_covered
        self.lines_covered = lines_covered
        self.lines_not_covered = lines_not_covered
        self.lines_partially_covered = lines_partially_covered
