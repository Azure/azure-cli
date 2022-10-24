# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=too-many-locals, too-many-statements, line-too-long
def load_arguments(self, _):
    with self.argument_context('dev') as c:
        # c.argument('help', action=None)
        c.positional('extra_options', nargs='*', default=[],
                     help="Other options which will be passed through to Azure Developer CLI as it is. "
                          "Please put all the extra options after a `--`. For example: `az dev -- init -e environment`")
