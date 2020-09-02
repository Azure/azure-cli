import os
import subprocess
from .reverse_dependency import get_dummy_cli


DUMMY = 'dummy'
INSTALLATION = 'installation'


class CLIContext(object):
    def __init__(self):
        self.test_mode = os.getenv('AZURE_CLI_TEST_MODE', DUMMY)
        if self.test_mode == INSTALLATION:
            if not os.getenv('AZURE_CLI_TEST_INSTALLATION_PATH'):
                raise AssertionError('Environment variable `AZURE_CLI_TEST_INSTALLATION_PATH` must be set when `AZURE_CLI_TEST_MODE` is set to `installation`')
            self.ctx = os.getenv('AZURE_CLI_TEST_INSTALLATION_PATH')
        else:
            self.ctx = get_dummy_cli()
    
    def clear_cache(self):
        if self.test_mode == DUMMY:
            self.ctx.data['_cache'] = None
    
    def invoke(self, args, out_file):
        if self.test_mode == DUMMY:
            return self.ctx.invoke(args, out_file=out_file)
        args.insert(0, self.ctx)
        return subprocess.call(args, stdout=out_file)
