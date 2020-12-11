# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def file_related_exception_handler(ex):
    from azure.cli.core.azclierror import FileOperationError
    if isinstance(ex, FileNotFoundError):
        raise FileOperationError(ex, recommendation='Please check the file path.')
    if isinstance(ex, PermissionError):
        raise FileOperationError(ex,
                                 recommendation='Please make sure you have enough permissions on the file/directory.')
    if isinstance(ex, IsADirectoryError):
        raise FileOperationError(ex, recommendation='File is expected, not a directory.')
    if isinstance(ex, NotADirectoryError):
        raise FileOperationError(ex, recommendation='Directory is expected, not a file.')
    import sys
    from six import reraise
    reraise(*sys.exc_info())
