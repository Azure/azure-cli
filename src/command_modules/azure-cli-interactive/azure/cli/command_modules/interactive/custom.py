# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.core.azlogging as azlogging


logger = azlogging.get_az_logger(__name__)


def start_shell(style=None):
    from azclishell.__main__ import main
    main(style=style)
