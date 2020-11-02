# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def file_related_exception_handler(ex):
    from azure.cli.core.azclierror import InvalidArgumentValueError
    if isinstance(ex, (FileNotFoundError, PermissionError, IsADirectoryError, OSError)):
        raise InvalidArgumentValueError(ex)
    import sys
    from six import reraise
    reraise(*sys.exc_info())
