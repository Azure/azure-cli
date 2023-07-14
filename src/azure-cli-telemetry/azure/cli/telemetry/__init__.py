# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os
import subprocess
import portalocker

from azure.cli.telemetry.util import save_payload

__version__ = "1.1.0"

DEFAULT_INSTRUMENTATION_KEY = 'c4395b75-49cc-422c-bc95-c7d51aef5d46'


def _start(config_dir):
    from azure.cli.telemetry.components.telemetry_logging import get_logger

    logger = get_logger('process')

    args = [sys.executable, os.path.realpath(__file__), config_dir]
    logger.info('Creating upload process: "%s %s %s"', *args)

    kwargs = {'args': args}
    if os.name == 'nt':
        # Windows process creation flag to not reuse the parent console.
        # Without this, the background service is associated with the
        # starting process's console, and will block that console from
        # exiting until the background service self-terminates.
        # Elsewhere, fork just does the right thing.
        kwargs['creationflags'] = 0x00000010  # CREATE_NEW_CONSOLE

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs['startupinfo'] = startupinfo
    else:
        if sys.version_info >= (3, 3):
            kwargs['stdin'] = subprocess.DEVNULL
            kwargs['stdout'] = subprocess.DEVNULL
            kwargs['stderr'] = subprocess.STDOUT

    subprocess.Popen(**kwargs)
    logger.info('Return from creating process')


def save(config_dir, payload):
    from azure.cli.telemetry.components.telemetry_client import CliTelemetryClient
    from azure.cli.telemetry.components.telemetry_logging import get_logger

    logger = get_logger('main')
    try:
        # Split payload to cli events and extra events by instrumentation key
        # extra events can be sent immediately
        # cli events will be handled in separate process
        import json
        events = json.loads(payload)

        logger.info('Begin splitting cli events and extra events, total events: %s', len(events))
        cli_events = {}
        client = CliTelemetryClient()
        for key, event in events.items():
            if key == DEFAULT_INSTRUMENTATION_KEY:
                cli_events[key] = event
            else:
                extra_event = {key: event}
                client.add(json.dumps(extra_event), flush=True)
        client.flush(force=True)
        cli_payload = json.dumps(cli_events) if cli_events else None
        logger.info('Finish splitting cli events and extra events, cli events: %s', len(cli_events))
    except Exception as ex:  # pylint: disable=broad-except
        logger.info("Split cli events and extra events failure: %s", str(ex))
        cli_payload = payload

    if save_payload(config_dir, cli_payload):
        logger.info('Begin creating telemetry upload process.')
        _start(config_dir)
        logger.info('Finish creating telemetry upload process.')


def main():
    from azure.cli.telemetry.components.telemetry_note import TelemetryNote
    from azure.cli.telemetry.components.records_collection import RecordsCollection
    from azure.cli.telemetry.components.telemetry_client import CliTelemetryClient
    from azure.cli.telemetry.components.telemetry_logging import config_logging_for_upload, get_logger

    try:
        config_dir = sys.argv[1]
        config_logging_for_upload(config_dir)

        logger = get_logger('main')
        logger.info('Attempt start. Configuration directory [%s].', sys.argv[1])

        try:
            with TelemetryNote(config_dir) as telemetry_note:
                telemetry_note.touch()

                collection = RecordsCollection(telemetry_note.get_last_sent(), config_dir)
                collection.snapshot_and_read()

                client = CliTelemetryClient()
                for each in collection:
                    client.add(each, flush=True)
                client.flush(force=True)

                telemetry_note.update_telemetry_note(collection.next_send)
        except portalocker.AlreadyLocked:
            # another upload process is running.
            logger.info('Lock out from note file under %s which means another process is running. Exit 0.', config_dir)
            sys.exit(0)
        except IOError as err:
            logger.warning('Unexpected IO Error %s. Exit 1.', err)
            sys.exit(1)
        except Exception as err:  # pylint: disable=broad-except
            logger.error('Unexpected Error %s. Exit 2.', err)
            logger.exception(err)
            sys.exit(2)
    except IndexError:
        sys.exit(1)


if __name__ == '__main__':
    main()
