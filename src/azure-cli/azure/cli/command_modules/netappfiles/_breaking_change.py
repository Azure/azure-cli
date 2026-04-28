# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.breaking_change import (
    register_argument_deprecate,
)
register_argument_deprecate('netappfiles volume create', '--is-default-quota-enabled',
                            redirect='netappfiles volume quota-rule')
register_argument_deprecate('netappfiles volume update', '--is-default-quota-enabled',
                            redirect='netappfiles volume quota-rule')
register_argument_deprecate('netappfiles volume create', '--default-group-quota-in-ki-bs',
                            redirect='netappfiles volume quota-rule')
register_argument_deprecate('netappfiles volume update', '--default-group-quota-in-ki-bs',
                            redirect='netappfiles volume quota-rule')
register_argument_deprecate('netappfiles volume create', '--default-user-quota-in-ki-bs',
                            redirect='netappfiles volume quota-rule')
register_argument_deprecate('netappfiles volume update', '--default-user-quota-in-ki-bs',
                            redirect='netappfiles volume quota-rule')
