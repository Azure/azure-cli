# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitPullRequestMergeOptions(Model):
    """GitPullRequestMergeOptions.

    :param detect_rename_false_positives:
    :type detect_rename_false_positives: bool
    :param disable_renames: If true, rename detection will not be performed during the merge.
    :type disable_renames: bool
    """

    _attribute_map = {
        'detect_rename_false_positives': {'key': 'detectRenameFalsePositives', 'type': 'bool'},
        'disable_renames': {'key': 'disableRenames', 'type': 'bool'}
    }

    def __init__(self, detect_rename_false_positives=None, disable_renames=None):
        super(GitPullRequestMergeOptions, self).__init__()
        self.detect_rename_false_positives = detect_rename_false_positives
        self.disable_renames = disable_renames
