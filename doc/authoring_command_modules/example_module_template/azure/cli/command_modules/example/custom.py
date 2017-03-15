# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.core.azlogging as azlogging


logger = azlogging.get_az_logger(__name__)


def example_custom(example_param=None):
    result = {'example_param': example_param}
    return result


def example_custom_two():
    return ['hello', 'world']
