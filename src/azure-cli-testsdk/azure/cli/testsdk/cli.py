# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import subprocess
from .reverse_dependency import get_dummy_cli


DUMMY = 'dummy'
INSTALLATION = 'installation'


class CLIContext(object):
    def __init__(self):
        self.test_mode = os.getenv('AZURE_CLI_TEST_MODE', DUMMY)
        if self.test_mode == DUMMY:
            self.ctx = get_dummy_cli()

    def clear_cache(self):
        if self.test_mode == DUMMY:
            self.ctx.data['_cache'] = None

    def invoke(self, args, out_file):
        if self.test_mode == DUMMY:
            return self.ctx.invoke(args, out_file=out_file)
        if len(args) > 0 and args[0] != 'az':
            args.insert(0, 'az')
        return subprocess.call(args, stdout=out_file)


def prepare_cli_context():
    return CLIContext()
