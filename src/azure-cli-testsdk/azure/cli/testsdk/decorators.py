# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


def api_version_constraint(cli_ctx, resource_type, **kwargs):
    return unittest.skipUnless(cli_ctx.cloud.supported_api_version(resource_type, **kwargs),
                               "Test not supported by current profile.")
