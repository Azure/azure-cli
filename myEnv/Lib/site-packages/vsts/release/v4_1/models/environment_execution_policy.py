# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class EnvironmentExecutionPolicy(Model):
    """EnvironmentExecutionPolicy.

    :param concurrency_count: This policy decides, how many environments would be with Environment Runner.
    :type concurrency_count: int
    :param queue_depth_count: Queue depth in the EnvironmentQueue table, this table keeps the environment entries till Environment Runner is free [as per it's policy] to take another environment for running.
    :type queue_depth_count: int
    """

    _attribute_map = {
        'concurrency_count': {'key': 'concurrencyCount', 'type': 'int'},
        'queue_depth_count': {'key': 'queueDepthCount', 'type': 'int'}
    }

    def __init__(self, concurrency_count=None, queue_depth_count=None):
        super(EnvironmentExecutionPolicy, self).__init__()
        self.concurrency_count = concurrency_count
        self.queue_depth_count = queue_depth_count
