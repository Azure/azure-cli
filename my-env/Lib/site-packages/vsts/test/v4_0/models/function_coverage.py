# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FunctionCoverage(Model):
    """FunctionCoverage.

    :param class_:
    :type class_: str
    :param name:
    :type name: str
    :param namespace:
    :type namespace: str
    :param source_file:
    :type source_file: str
    :param statistics:
    :type statistics: :class:`CoverageStatistics <test.v4_0.models.CoverageStatistics>`
    """

    _attribute_map = {
        'class_': {'key': 'class', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'namespace': {'key': 'namespace', 'type': 'str'},
        'source_file': {'key': 'sourceFile', 'type': 'str'},
        'statistics': {'key': 'statistics', 'type': 'CoverageStatistics'}
    }

    def __init__(self, class_=None, name=None, namespace=None, source_file=None, statistics=None):
        super(FunctionCoverage, self).__init__()
        self.class_ = class_
        self.name = name
        self.namespace = namespace
        self.source_file = source_file
        self.statistics = statistics
