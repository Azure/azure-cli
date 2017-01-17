# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import ParametersContext, patch_arg_make_required


with ParametersContext(command='sql server create') as c:
    from azure.mgmt.sql.models.server import Server

    # About the patches:
    #
    # - Both administrator_login and administrator_login_password are required for server creation.
    # However these two parameters are given default value in the create_or_update function
    # signature, therefore, they can't be automatically converted to requirement arguments.
    c.expand('parameters', Server, group_name='Creating', patches={
        'administrator_login': patch_arg_make_required,
        'administrator_login_password': patch_arg_make_required
    })

with ParametersContext(command='sql database create') as c:
    from azure.mgmt.sql.models.database import Database

    c.expand('parameters', Database, group_name='Creating')
