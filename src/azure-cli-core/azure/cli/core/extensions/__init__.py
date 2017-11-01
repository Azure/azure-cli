# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.extensions.transform import register as register_transform


def register_extensions(cli_ctx):
    register_transform(cli_ctx)
