# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.core.azlogging as azlogging


logger = azlogging.get_az_logger(__name__)
in_shell = False

def start_shell(style=None):
    global in_shell
    if in_shell:
        print("You're in the interactive shell already!!\n")
        return
    else:
        in_shell = True
    from azclishell.__main__ import main
    main(style=style)
    in_shell = False
