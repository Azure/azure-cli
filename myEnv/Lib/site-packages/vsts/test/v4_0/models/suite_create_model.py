# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SuiteCreateModel(Model):
    """SuiteCreateModel.

    :param name:
    :type name: str
    :param query_string:
    :type query_string: str
    :param requirement_ids:
    :type requirement_ids: list of int
    :param suite_type:
    :type suite_type: str
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'query_string': {'key': 'queryString', 'type': 'str'},
        'requirement_ids': {'key': 'requirementIds', 'type': '[int]'},
        'suite_type': {'key': 'suiteType', 'type': 'str'}
    }

    def __init__(self, name=None, query_string=None, requirement_ids=None, suite_type=None):
        super(SuiteCreateModel, self).__init__()
        self.name = name
        self.query_string = query_string
        self.requirement_ids = requirement_ids
        self.suite_type = suite_type
