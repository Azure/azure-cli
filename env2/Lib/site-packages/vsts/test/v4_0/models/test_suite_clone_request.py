# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestSuiteCloneRequest(Model):
    """TestSuiteCloneRequest.

    :param clone_options:
    :type clone_options: :class:`CloneOptions <test.v4_0.models.CloneOptions>`
    :param destination_suite_id:
    :type destination_suite_id: int
    :param destination_suite_project_name:
    :type destination_suite_project_name: str
    """

    _attribute_map = {
        'clone_options': {'key': 'cloneOptions', 'type': 'CloneOptions'},
        'destination_suite_id': {'key': 'destinationSuiteId', 'type': 'int'},
        'destination_suite_project_name': {'key': 'destinationSuiteProjectName', 'type': 'str'}
    }

    def __init__(self, clone_options=None, destination_suite_id=None, destination_suite_project_name=None):
        super(TestSuiteCloneRequest, self).__init__()
        self.clone_options = clone_options
        self.destination_suite_id = destination_suite_id
        self.destination_suite_project_name = destination_suite_project_name
