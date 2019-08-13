# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.util import CLIError


def validate_cluster_args(namespace):
    max_name_length = 22
    name_length = len(namespace.cluster_name)
    if name_length > max_name_length:
        raise CLIError('name can not be longer then ' + str(max_name_length) + " letters")
