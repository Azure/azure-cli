# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_argument_deprecate

register_argument_deprecate('mysql flexible-server create', '--storage-redundancy')
register_argument_deprecate('mysql flexible-server restore', '--storage-redundancy')
register_argument_deprecate('mysql flexible-server geo-restore', '--storage-redundancy')
register_argument_deprecate('mysql flexible-server replica create', '--storage-redundancy')
