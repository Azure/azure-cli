# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['configure'] = """
    type: command
    short-summary: Display and manage the Azure CLI 2.0 configuration. This command is interactive.
    parameters:
        - name: --defaults -d
          short-summary: >
            Space separated 'name=value' pairs for common argument defaults.
    examples:
        - name: Set default resource group, webapp and VM names.
          text: az configure --defaults group=myRG web=myweb vm=myvm
        - name: Clear default webapp and VM names.
          text: az configure --defaults vm='' web=''
"""
