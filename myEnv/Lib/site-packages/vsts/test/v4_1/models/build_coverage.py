# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BuildCoverage(Model):
    """BuildCoverage.

    :param code_coverage_file_url:
    :type code_coverage_file_url: str
    :param configuration:
    :type configuration: :class:`BuildConfiguration <test.v4_1.models.BuildConfiguration>`
    :param last_error:
    :type last_error: str
    :param modules:
    :type modules: list of :class:`ModuleCoverage <test.v4_1.models.ModuleCoverage>`
    :param state:
    :type state: str
    """

    _attribute_map = {
        'code_coverage_file_url': {'key': 'codeCoverageFileUrl', 'type': 'str'},
        'configuration': {'key': 'configuration', 'type': 'BuildConfiguration'},
        'last_error': {'key': 'lastError', 'type': 'str'},
        'modules': {'key': 'modules', 'type': '[ModuleCoverage]'},
        'state': {'key': 'state', 'type': 'str'}
    }

    def __init__(self, code_coverage_file_url=None, configuration=None, last_error=None, modules=None, state=None):
        super(BuildCoverage, self).__init__()
        self.code_coverage_file_url = code_coverage_file_url
        self.configuration = configuration
        self.last_error = last_error
        self.modules = modules
        self.state = state
