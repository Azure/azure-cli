# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------s

from azure.cli.core.commands.parameters import get_enum_type, name_type, tags_type, \
    get_generic_completion_list, get_three_state_flag, get_resource_name_completion_list
from azure.cli.core.util import get_json_object


# pylint: disable=too-many-statements
def load_arguments(self, _):
    from knack.arguments import CLIArgumentType

    # spark batch
    with self.argument_context("synapse spark-batch") as c:
        c.argument('workspace_name', arg_type=name_type, help='The name of the workspace.')
        c.argument('sparkpool_name', arg_type=name_type, help='The name of the spark pool.')
        c.argument('batch_id', arg_group='Spark Batch', help='The id of the spark batch job')