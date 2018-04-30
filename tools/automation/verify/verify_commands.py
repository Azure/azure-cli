# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import logging
import subprocess
import sys
import asyncio
from itertools import islice


def init(root):
    parser = root.add_parser('commands', help='Run all the commands with "-h" parameter.')
    parser.add_argument('--prefix', dest='prefix',
                        help='Select the commands with the given prefix. If omit select all the commands.')
    parser.add_argument('--list-only', dest='list_only', action='store_true',
                        help='List the commands\' information instead of execute them in separate processes.')
    parser.add_argument('--details', dest='details', action='store_true',
                        help='List the commands\' details. Use with --list-only.')
    parser.set_defaults(func=run_commands)
    parser.set_defaults(func=run_commands)


def run_commands(args):
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

    if args.prefix:
        table = dict((each, table[each]) for each in table if each.startswith(args.prefix))

    if args.list_only:
        for each in sorted(table):
            if args.details:
                print_command_info(table[each])
            else:
                print(each)
        sys.exit(0)

    commands = ['az {} --help'.format(each) for each in table]
    print('{} commands to test.'.format(len(commands)))

    loop = asyncio.get_event_loop()
    failures = loop.run_until_complete(
        run_commands_in_parallel(
            (run_one_command(c) for c in commands),
            parallism=os.cpu_count() * 4
        )
    )

    if failures:
        for command, exit_code in failures:
            print('Failed command {}. Exit code: {}.'.format(command, exit_code, stdout))
        sys.exit(1)

    print('Done')


async def run_commands_in_parallel(coroutines, parallism=10):
    futures = [asyncio.ensure_future(c) for c in islice(coroutines, 0, parallism)]
    async def return_while_run():
        while True:
            await asyncio.sleep(0)
            for f in futures:
                if f.done():
                    futures.remove(f)
                    try:
                        futures.append(asyncio.ensure_future(next(coroutines)))
                    except StopIteration:
                        pass
                    return f.result()
    failures = []
    while futures:
        c, e = await return_while_run()
        sys.stdout.write('{} {}\n'.format('PASS' if e == 0 else 'FAIL', c))
        sys.stdout.flush()
        if e != 0:
            failures.append((c, e))

    return failures


async def run_one_command(command):
    process = await asyncio.create_subprocess_shell(command,
                                                    stdout=asyncio.subprocess.PIPE,
                                                    stderr=asyncio.subprocess.STDOUT)
    await process.wait()
    return command, process.returncode


def print_command_info(command):
    from tabulate import tabulate

    command.load_arguments()

    print('\n{}\n'.format(command.name.upper()))

    attributes = []
    for attr in dir(command):
        if attr.startswith('__'):
            continue

        value = getattr(command, attr)
        if isinstance(value, dict):
            attributes.append({'name': '{}'.format(attr), 'value': ''})
            for k in value:
                attributes.append({'name': '...{}'.format(str(k)), 'value': value[k]})
        else:
            value = str(value)
            attributes.append({'name': attr, 'value': value})

    print(tabulate(attributes, tablefmt='plain'))
    print('<<<<')
