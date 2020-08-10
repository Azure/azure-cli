# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .operation_reference import OperationReference


class UserEntitlementOperationReference(OperationReference):
    """UserEntitlementOperationReference.

    :param id: Unique identifier for the operation.
    :type id: str
    :param plugin_id: Unique identifier for the plugin.
    :type plugin_id: str
    :param status: The current status of the operation.
    :type status: object
    :param url: URL to get the full operation object.
    :type url: str
    :param completed: Operation completed with success or failure.
    :type completed: bool
    :param have_results_succeeded: True if all operations were successful.
    :type have_results_succeeded: bool
    :param results: List of results for each operation.
    :type results: list of :class:`UserEntitlementOperationResult <member-entitlement-management.v4_1.models.UserEntitlementOperationResult>`
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'plugin_id': {'key': 'pluginId', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'},
        'completed': {'key': 'completed', 'type': 'bool'},
        'have_results_succeeded': {'key': 'haveResultsSucceeded', 'type': 'bool'},
        'results': {'key': 'results', 'type': '[UserEntitlementOperationResult]'}
    }

    def __init__(self, id=None, plugin_id=None, status=None, url=None, completed=None, have_results_succeeded=None, results=None):
        super(UserEntitlementOperationReference, self).__init__(id=id, plugin_id=plugin_id, status=status, url=url)
        self.completed = completed
        self.have_results_succeeded = have_results_succeeded
        self.results = results
