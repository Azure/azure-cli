# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_other_breaking_change

register_other_breaking_change('sf managed-application update',
                               'Options list has changed, run help command to see allowed options')
