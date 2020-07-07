import inspect
import logging
import os
import sys
from argparse import ArgumentTypeError
from collections import OrderedDict, deque
from pathlib import Path
from threading import Event, Semaphore, Thread

import tox
from tox.config.cli.parser import ToxParser
from tox.plugin.impl import impl
from tox.session.common import env_list_flag
from tox.session.state import State
from tox.util.cpu import auto_detect_cpus
from tox.util.spinner import Spinner

from .common import env_run_create_flags

logger = logging.getLogger(__name__)

ENV_VAR_KEY = "TOX_PARALLEL_ENV"
OFF_VALUE = 0
DEFAULT_PARALLEL = OFF_VALUE
MAIN_FILE = Path(inspect.getsourcefile(tox)) / "__main__.py"


@impl
def tox_add_option(parser: ToxParser):
    our = parser.add_command("run-parallel", ["p"], "run environments in parallel", run_parallel)
    env_list_flag(our)
    env_run_create_flags(our)

    def parse_num_processes(str_value):
        if str_value == "all":
            return None
        if str_value == "auto":
            return auto_detect_cpus()
        else:
            value = int(str_value)
            if value < 0:
                raise ArgumentTypeError("value must be positive")
            return value

    our.add_argument(
        "-p",
        "--parallel",
        dest="parallel",
        help="run tox environments in parallel, the argument controls limit: all,"
        " auto - cpu count, some positive number, zero is turn off",
        action="store",
        type=parse_num_processes,
        default=DEFAULT_PARALLEL,
        metavar="VAL",
    )
    our.add_argument(
        "-o",
        "--parallel-live",
        action="store_true",
        dest="parallel_live",
        help="connect to stdout while running environments",
    )


def run_parallel(state: State):
    """here we'll just start parallel sub-processes"""
    live_out = state.options.parallel_live
    disable_spinner = bool(os.environ.get("TOX_PARALLEL_NO_SPINNER") == "1")
    args = [sys.executable, MAIN_FILE] + state.args
    try:
        position = args.index("--")
    except ValueError:
        position = len(args)

    max_parallel = state.options.parallel
    if max_parallel is None:
        max_parallel = len(state.tox_envs)
    semaphore = Semaphore(max_parallel)
    finished = Event()

    show_progress = not disable_spinner and not live_out and state.options.verbosity > 2

    with Spinner(enabled=show_progress) as spinner:

        def run_in_thread(tox_env, os_env, process_dict):
            output = None
            env_name = tox_env.envconfig.envname
            status = "skipped tests" if state.options.no_test else None
            try:
                os_env[str(ENV_VAR_KEY)] = str(env_name)
                args_sub = list(args)
                if hasattr(tox_env, "package"):
                    args_sub.insert(position, str(tox_env.perform_packaging))
                    args_sub.insert(position, "--installpkg")
                if tox_env.get_result_json_path():
                    result_json_index = args_sub.index("--result-json")
                    args_sub[result_json_index + 1] = f"{tox_env.get_result_json_path()}"
                with tox_env.new_action(f"parallel {tox_env.name}") as action:

                    def collect_process(process):
                        process_dict[tox_env] = (action, process)

                    print_out = not live_out and tox_env.envconfig.parallel_show_output
                    output = action.popen(
                        args=args_sub,
                        env=os_env,
                        redirect=not live_out,
                        capture_err=print_out,
                        callback=collect_process,
                        returnout=print_out,
                    )

            except Exception as err:
                status = f"parallel child exit code {err.exit_code}"
            finally:
                semaphore.release()
                finished.set()
                tox_env.status = status
                done.add(env_name)
                outcome = spinner.succeed
                if state.options.notest:
                    outcome = spinner.skip
                elif status is not None:
                    outcome = spinner.fail
                outcome(env_name)
                if print_out and output is not None:
                    logger.warning(output)

        threads = deque()
        processes = {}
        todo_keys = set(state.env_list)
        todo = OrderedDict((n, todo_keys & set(v.envconfig.depends)) for n, v in state.tox_envs.items())
        done = set()
        try:
            while todo:
                for name, depends in list(todo.items()):
                    if depends - done:
                        # skip if has unfinished dependencies
                        continue
                    del todo[name]
                    venv = state.tox_envs[name]
                    semaphore.acquire()
                    spinner.add(name)
                    thread = Thread(target=run_in_thread, args=(venv, os.environ.copy(), processes))
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
                if todo:
                    # wait until someone finishes and retry queuing jobs
                    finished.wait()
                    finished.clear()
            while threads:
                threads = [thread for thread in threads if not thread.join(0.1) and thread.is_alive()]
        except KeyboardInterrupt:
            logger.error(f"[{os.getpid()}] KeyboardInterrupt parallel - stopping children")
            while True:
                # do not allow to interrupt until children interrupt
                try:
                    # putting it inside a thread so it's not interrupted
                    stopper = Thread(target=_stop_child_processes, args=(processes, threads))
                    stopper.start()
                    stopper.join()
                except KeyboardInterrupt:
                    continue
                raise KeyboardInterrupt


def _stop_child_processes(processes, main_threads):
    """A three level stop mechanism for children - INT (250ms) -> TERM (100ms) -> KILL"""

    # first stop children
    # noinspection PyUnusedLocal
    def shutdown(tox_env, action, process):
        action.handle_interrupt(process)

    threads = [Thread(target=shutdown, args=(n, a, p)) for n, (a, p) in processes.items()]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # then its threads
    for thread in main_threads:
        thread.join()
