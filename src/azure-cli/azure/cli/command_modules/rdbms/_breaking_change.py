# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_logic_breaking_change


register_logic_breaking_change('postgres flexible-server create', 'Update default value of "--sku-name"',
                               detail='The default value will be changed from "Standard_D2s_v3" to a '
                               'supported sku based on regional capabilities.')
