# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import

helps['lab vm hibernate'] = """
type: command
short-summary: Hibernate a virtual machine.
examples:
  - name: Hibernate a virtual machine.
    text: az lab vm hibernate --resource-group MyResourceGroup --lab-name MyLab --name MyVM
"""