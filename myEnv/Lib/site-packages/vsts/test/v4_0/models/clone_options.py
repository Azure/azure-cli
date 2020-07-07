# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CloneOptions(Model):
    """CloneOptions.

    :param clone_requirements: If set to true requirements will be cloned
    :type clone_requirements: bool
    :param copy_all_suites: copy all suites from a source plan
    :type copy_all_suites: bool
    :param copy_ancestor_hierarchy: copy ancestor hieracrchy
    :type copy_ancestor_hierarchy: bool
    :param destination_work_item_type: Name of the workitem type of the clone
    :type destination_work_item_type: str
    :param override_parameters: Key value pairs where the key value is overridden by the value.
    :type override_parameters: dict
    :param related_link_comment: Comment on the link that will link the new clone  test case to the original Set null for no comment
    :type related_link_comment: str
    """

    _attribute_map = {
        'clone_requirements': {'key': 'cloneRequirements', 'type': 'bool'},
        'copy_all_suites': {'key': 'copyAllSuites', 'type': 'bool'},
        'copy_ancestor_hierarchy': {'key': 'copyAncestorHierarchy', 'type': 'bool'},
        'destination_work_item_type': {'key': 'destinationWorkItemType', 'type': 'str'},
        'override_parameters': {'key': 'overrideParameters', 'type': '{str}'},
        'related_link_comment': {'key': 'relatedLinkComment', 'type': 'str'}
    }

    def __init__(self, clone_requirements=None, copy_all_suites=None, copy_ancestor_hierarchy=None, destination_work_item_type=None, override_parameters=None, related_link_comment=None):
        super(CloneOptions, self).__init__()
        self.clone_requirements = clone_requirements
        self.copy_all_suites = copy_all_suites
        self.copy_ancestor_hierarchy = copy_ancestor_hierarchy
        self.destination_work_item_type = destination_work_item_type
        self.override_parameters = override_parameters
        self.related_link_comment = related_link_comment
