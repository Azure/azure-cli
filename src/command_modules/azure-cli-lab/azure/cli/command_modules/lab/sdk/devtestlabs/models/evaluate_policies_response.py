# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class EvaluatePoliciesResponse(Model):
    """Response body for evaluating a policy set.

    :param results: Results of evaluating a policy set.
    :type results: list of :class:`PolicySetResult
     <azure.mgmt.devtestlabs.models.PolicySetResult>`
    """

    _attribute_map = {
        'results': {'key': 'results', 'type': '[PolicySetResult]'},
    }

    def __init__(self, results=None):
        self.results = results
