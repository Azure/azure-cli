# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CloneStatistics(Model):
    """CloneStatistics.

    :param cloned_requirements_count: Number of Requirments cloned so far.
    :type cloned_requirements_count: int
    :param cloned_shared_steps_count: Number of shared steps cloned so far.
    :type cloned_shared_steps_count: int
    :param cloned_test_cases_count: Number of test cases cloned so far
    :type cloned_test_cases_count: int
    :param total_requirements_count: Total number of requirements to be cloned
    :type total_requirements_count: int
    :param total_test_cases_count: Total number of test cases to be cloned
    :type total_test_cases_count: int
    """

    _attribute_map = {
        'cloned_requirements_count': {'key': 'clonedRequirementsCount', 'type': 'int'},
        'cloned_shared_steps_count': {'key': 'clonedSharedStepsCount', 'type': 'int'},
        'cloned_test_cases_count': {'key': 'clonedTestCasesCount', 'type': 'int'},
        'total_requirements_count': {'key': 'totalRequirementsCount', 'type': 'int'},
        'total_test_cases_count': {'key': 'totalTestCasesCount', 'type': 'int'}
    }

    def __init__(self, cloned_requirements_count=None, cloned_shared_steps_count=None, cloned_test_cases_count=None, total_requirements_count=None, total_test_cases_count=None):
        super(CloneStatistics, self).__init__()
        self.cloned_requirements_count = cloned_requirements_count
        self.cloned_shared_steps_count = cloned_shared_steps_count
        self.cloned_test_cases_count = cloned_test_cases_count
        self.total_requirements_count = total_requirements_count
        self.total_test_cases_count = total_test_cases_count
