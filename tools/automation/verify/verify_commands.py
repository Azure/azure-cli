# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import multiprocessing
import sys
import subprocess


def init(root):
    parser = root.add_parser('commands', help='Run all the commands with "-h" parameter.')
    parser.set_defaults(func=run_commands)


def run_commands(_):
    from knack.cli import CLI
    from azure.cli.core import MainCommandsLoader, logger
    from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX
    from azure.cli.core.cloud import get_active_cloud

    class MockCLI(CLI):
        def __init__(self):
            super(MockCLI, self).__init__(
                cli_name='mock_cli',
                config_dir=GLOBAL_CONFIG_DIR,
                config_env_var_prefix=ENV_VAR_PREFIX)
            self.cloud = get_active_cloud(self)

    logger.addHandler(logging.NullHandler())

    loader = MainCommandsLoader(MockCLI())
    table = loader.load_command_table('')
    commands = ['az {} --help'.format(each) for each in table]
    results = []

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    for i, res in enumerate(pool.imap_unordered(run_single_command, commands, 10), 1):
        sys.stderr.write('{:.2f}% \n'.format(float(i) * 100 / len(commands)))
        sys.stderr.flush()
        results.append(res)
    pool.close()
    pool.join()

    if not all(results):
        sys.stderr.write('Error running --help on commands.\n')
        sys.exit(1)

    print('Done')


def run_single_command(command):
    execution_error = None
    for i in range(3):  # retry the command 3 times
        try:
            subprocess.check_output(command.split(), stderr=subprocess.STDOUT, universal_newlines=True)
            return True
        except subprocess.CalledProcessError as error:
            execution_error = error
            continue

    if execution_error:
        sys.stderr.write('Failed {} -> \n{} / {} \n'.format(command, execution_error.output, str(execution_error)))

    return False
