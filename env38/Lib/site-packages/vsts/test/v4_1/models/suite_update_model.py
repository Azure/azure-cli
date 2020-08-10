# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SuiteUpdateModel(Model):
    """SuiteUpdateModel.

    :param default_configurations:
    :type default_configurations: list of :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param default_testers:
    :type default_testers: list of :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param inherit_default_configurations:
    :type inherit_default_configurations: bool
    :param name:
    :type name: str
    :param parent:
    :type parent: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param query_string:
    :type query_string: str
    """

    _attribute_map = {
        'default_configurations': {'key': 'defaultConfigurations', 'type': '[ShallowReference]'},
        'default_testers': {'key': 'defaultTesters', 'type': '[ShallowReference]'},
        'inherit_default_configurations': {'key': 'inheritDefaultConfigurations', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'parent': {'key': 'parent', 'type': 'ShallowReference'},
        'query_string': {'key': 'queryString', 'type': 'str'}
    }

    def __init__(self, default_configurations=None, default_testers=None, inherit_default_configurations=None, name=None, parent=None, query_string=None):
        super(SuiteUpdateModel, self).__init__()
        self.default_configurations = default_configurations
        self.default_testers = default_testers
        self.inherit_default_configurations = inherit_default_configurations
        self.name = name
        self.parent = parent
        self.query_string = query_string
