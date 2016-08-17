#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.help_files import helps #pylint: disable=unused-import
import os

#pylint: disable=line-too-long

help_path = os.path.realpath(__file__).replace("\\", "/") 

helps['resource'] = """
            doc-source: {0}
""".format(help_path)

helps['tag'] = """
            doc-source: {0}
""".format(help_path)

helps['resource policy create'] = """
            type: command
            short-summary: Create a policy 
            parameters: 
                - name: --rules
                  type: string
                  short-summary: 'JSON formatted string or a path to a file with such content'
            examples:
                - name: Create a policy with following rules
                  text: |
                        {
                            "if": 
                            {
                                "source": "action",
                                "equals": "Microsoft.Storage/storageAccounts/write"
                            },
                            "then":
                            {
                                "effect": "deny"
                            }
                        }
            """
