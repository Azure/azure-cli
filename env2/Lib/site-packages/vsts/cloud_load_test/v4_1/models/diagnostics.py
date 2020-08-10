# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Diagnostics(Model):
    """Diagnostics.

    :param diagnostic_store_connection_string:
    :type diagnostic_store_connection_string: str
    :param last_modified_time:
    :type last_modified_time: datetime
    :param relative_path_to_diagnostic_files:
    :type relative_path_to_diagnostic_files: str
    """

    _attribute_map = {
        'diagnostic_store_connection_string': {'key': 'diagnosticStoreConnectionString', 'type': 'str'},
        'last_modified_time': {'key': 'lastModifiedTime', 'type': 'iso-8601'},
        'relative_path_to_diagnostic_files': {'key': 'relativePathToDiagnosticFiles', 'type': 'str'}
    }

    def __init__(self, diagnostic_store_connection_string=None, last_modified_time=None, relative_path_to_diagnostic_files=None):
        super(Diagnostics, self).__init__()
        self.diagnostic_store_connection_string = diagnostic_store_connection_string
        self.last_modified_time = last_modified_time
        self.relative_path_to_diagnostic_files = relative_path_to_diagnostic_files
