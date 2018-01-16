# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError


logger = get_logger(__name__)


def create_example(cmd, example_name, resource_group_name, location=None):
    from azure.mgmt.example.models import Example
    from azure.cli.command_modules.example._client_factory import cf_example
    client = cf_example(cmd.cli_ctx)

    # TODO: Your custom logic here

    example = Example(location=location)
    return client.create_or_update(example_name, resource_group_name, example)
