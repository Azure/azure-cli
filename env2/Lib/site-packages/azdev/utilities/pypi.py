# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib


def is_available_on_pypi(module_name, module_version):
    client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
    available_versions = client.package_releases(module_name, True)
    return module_version in available_versions
