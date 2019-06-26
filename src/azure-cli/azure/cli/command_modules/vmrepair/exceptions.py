# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class AzCommandError(Exception):
    """Raised when az command called and returns error"""


class SkuNotAvailableError(Exception):
    """Raised when unable to find compatible SKU for repair VM"""


class UnmanagedDiskCopyError(Exception):
    """Raised when error occured during unmanaged disk copy"""


class WindowsOsNotAvailableError(Exception):
    """Raised the Windows image not available from gallery."""
