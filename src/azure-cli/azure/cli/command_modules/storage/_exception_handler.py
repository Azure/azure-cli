# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def file_related_exception_handler(ex):
    from azure.cli.core.azclierror import (AzFileNotFoundError, AzPermissionError, AzIsADirectoryError, AzOSError)
    if isinstance(ex, FileNotFoundError):
        raise AzFileNotFoundError(ex)
    if isinstance(ex, PermissionError):
        raise AzPermissionError(ex)
    if isinstance(ex, IsADirectoryError):
        raise AzIsADirectoryError(ex)
    if isinstance(ex, OSError):
        raise AzOSError(ex)
    import sys
    from six import reraise
    reraise(*sys.exc_info())
