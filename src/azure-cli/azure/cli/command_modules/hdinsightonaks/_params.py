# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#
# Code generated by aaz-dev-tools
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements


def load_arguments(self, _):  # pylint: disable=unused-argument
    with self.argument_context('hdinsight-on-aks cluster node-profile create') as c:
        c.argument('count',
                   help='The number of virtual machines.', required=True)
        c.argument('node_type',
                   help='The node type.', required=True)
        c.argument('vm_size',
                   help='The virtual machine SKU.', required=True)