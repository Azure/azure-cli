# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def get_sp_create_output_xml(result):
    return print('\n'.join(['<add key=\"{}\" value=\"{}\" />'.format(k, v) for k, v in result.items()]))
