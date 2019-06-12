# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_arguments(self, _):
    with self.argument_context('find') as c:
        c.positional('cli_term', help='An Azure CLI command or group for which you need an example.')
