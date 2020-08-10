# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NpmPackagesBatchRequest(Model):
    """NpmPackagesBatchRequest.

    :param data: Data required to perform the operation. This is optional based on type of operation. Use BatchPromoteData if performing a promote operation.
    :type data: :class:`BatchOperationData <npm.v4_1.models.BatchOperationData>`
    :param operation: Type of operation that needs to be performed on packages.
    :type operation: object
    :param packages: The packages onto which the operation will be performed.
    :type packages: list of :class:`MinimalPackageDetails <npm.v4_1.models.MinimalPackageDetails>`
    """

    _attribute_map = {
        'data': {'key': 'data', 'type': 'BatchOperationData'},
        'operation': {'key': 'operation', 'type': 'object'},
        'packages': {'key': 'packages', 'type': '[MinimalPackageDetails]'}
    }

    def __init__(self, data=None, operation=None, packages=None):
        super(NpmPackagesBatchRequest, self).__init__()
        self.data = data
        self.operation = operation
        self.packages = packages
