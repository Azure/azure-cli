#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.help_files import helps #pylint: disable=unused-import
import os

#pylint: disable=line-too-long

help_path = os.path.realpath(__file__).replace("\\", "/") 

helps['keyvault'] = """
            doc-source: {0}
""".format(help_path)
