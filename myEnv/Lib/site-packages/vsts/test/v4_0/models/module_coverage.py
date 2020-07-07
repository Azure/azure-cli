# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ModuleCoverage(Model):
    """ModuleCoverage.

    :param block_count:
    :type block_count: int
    :param block_data:
    :type block_data: str
    :param functions:
    :type functions: list of :class:`FunctionCoverage <test.v4_0.models.FunctionCoverage>`
    :param name:
    :type name: str
    :param signature:
    :type signature: str
    :param signature_age:
    :type signature_age: int
    :param statistics:
    :type statistics: :class:`CoverageStatistics <test.v4_0.models.CoverageStatistics>`
    """

    _attribute_map = {
        'block_count': {'key': 'blockCount', 'type': 'int'},
        'block_data': {'key': 'blockData', 'type': 'str'},
        'functions': {'key': 'functions', 'type': '[FunctionCoverage]'},
        'name': {'key': 'name', 'type': 'str'},
        'signature': {'key': 'signature', 'type': 'str'},
        'signature_age': {'key': 'signatureAge', 'type': 'int'},
        'statistics': {'key': 'statistics', 'type': 'CoverageStatistics'}
    }

    def __init__(self, block_count=None, block_data=None, functions=None, name=None, signature=None, signature_age=None, statistics=None):
        super(ModuleCoverage, self).__init__()
        self.block_count = block_count
        self.block_data = block_data
        self.functions = functions
        self.name = name
        self.signature = signature
        self.signature_age = signature_age
        self.statistics = statistics
