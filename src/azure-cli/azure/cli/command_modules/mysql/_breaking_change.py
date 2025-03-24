# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.breaking_change import register_logic_breaking_change

register_logic_breaking_change('mysql flexible-server create', 'Update the validator',
                               detail='the argument `--high-availability` will no longer accept value `SameZone` for '
                               'new servers created in Business-Critical service tier '
                               'if the region supports multiple zones.')
register_logic_breaking_change('mysql flexible-server update', 'Update the validator',
                               detail='the argument `--high-availability` will no longer accept value `SameZone` for '
                               'new servers created in Business-Critical service tier '
                               'if the region supports multiple zones.')
