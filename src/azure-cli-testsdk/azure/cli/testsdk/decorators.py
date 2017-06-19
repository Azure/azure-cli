# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.profiles import supported_api_version


def api_version_constraint(resource_type, **kwargs):
    return unittest.skipUnless(supported_api_version(resource_type, **kwargs),
                               "Test not supported by current profile.")
