# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_other_breaking_change

# --min-tls-version removing version 1.0 1.1
register_other_breaking_change('storage account create',
                               message='The --min-tls-version argument values TLS1_0 and TLS1_1 have been retired on'
                                       ' 2026/02/03 and will be removed on 2026/03/03.')
register_other_breaking_change('storage account update',
                               message='The --min-tls-version argument values TLS1_0 and TLS1_1 have been retired on'
                                       ' 2026/02/03 and will be removed on 2026/03/03.')
