# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.extensions.query import register as register_query
from azure.cli.core.extensions.transform import register as register_transform


def register_extensions(application):
    register_query(application)
    register_transform(application)
