# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import ParametersContext, patch_arg_make_required, patch_arg_update_description


with ParametersContext(command='sql server create') as c:
    from azure.mgmt.sql.models.server import Server

    # About the patches:
    #
    # - Both administrator_login and administrator_login_password are required for server creation.
    # However these two parameters are given default value in the create_or_update function
    # signature, therefore, they can't be automatically converted to requirement arguments.
    #
    # - Due to issue https://github.com/Azure/azure-cli/issues/1644, the description of version
    # can't be correctly extracted
    #
    c.expand('parameters', Server, patches={
        'administrator_login': patch_arg_make_required,
        'administrator_login_password': patch_arg_make_required,
        'version': patch_arg_update_description(
            "The version of the server, possible values include: '2.0', '12.0'.")
    })

