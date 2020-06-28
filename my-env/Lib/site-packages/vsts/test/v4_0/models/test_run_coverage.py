# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestRunCoverage(Model):
    """TestRunCoverage.

    :param last_error:
    :type last_error: str
    :param modules:
    :type modules: list of :class:`ModuleCoverage <test.v4_0.models.ModuleCoverage>`
    :param state:
    :type state: str
    :param test_run:
    :type test_run: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    """

    _attribute_map = {
        'last_error': {'key': 'lastError', 'type': 'str'},
        'modules': {'key': 'modules', 'type': '[ModuleCoverage]'},
        'state': {'key': 'state', 'type': 'str'},
        'test_run': {'key': 'testRun', 'type': 'ShallowReference'}
    }

    def __init__(self, last_error=None, modules=None, state=None, test_run=None):
        super(TestRunCoverage, self).__init__()
        self.last_error = last_error
        self.modules = modules
        self.state = state
        self.test_run = test_run
