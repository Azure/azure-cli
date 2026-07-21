# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Helper imports for the Azure DevOps Keyring module.
"""

# *********************************************************
# Import the correct urlsplit function

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit


# *********************************************************
# Import (and possibly update) subprocess.Popen

from subprocess import Popen

if not hasattr(Popen, "__enter__"):
    # Handle Python 2.x not making Popen a context manager
    class Popen(Popen):
        def __enter__(self):
            return self

        def __exit__(self, ex_type, ex_value, ex_tb):
            pass
