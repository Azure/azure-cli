# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""Table transformer for keyvault commands"""

from azure.cli.core.commands.transform import build_table_output


def transform_secret_list(result):
    return build_table_output(result, [
        ('Name', 'name'),
        ('Id', 'id'),
        ('ContentType', 'contentType'),
        ('Enabled', 'attributes.enabled'),
        ('Expires', 'attributes.expires')
    ])
