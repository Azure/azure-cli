# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


"""
A light-weight ARM client.
"""

from ._arm_client import ARMClient, ARMError

__all__ = [
    "ARMClient",
    "ARMError"
]
