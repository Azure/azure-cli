# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


def api_version_constraint(resource_type, **kwargs):
    from azure.cli.core.profiles import supported_api_version
    from azure.cli.testsdk import TestCli
    cli_ctx = TestCli()
    return unittest.skipUnless(supported_api_version(cli_ctx, resource_type, **kwargs),
                               "Test not supported by current profile.")
