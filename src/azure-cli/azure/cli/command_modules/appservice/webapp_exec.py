# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core.azclierror import ResourceNotFoundError, ValidationError, AzureConnectionError

from ._appservice_utils import _generic_site_operation
from .custom import _get_scm_url, get_scm_site_headers, list_instances
from .utils import is_linux_webapp

logger = get_logger(__name__)

_MAX_SHELL_PATH_LENGTH = 256


def webapp_exec(cmd,
                resource_group_name,
                name,
                command=None,
                args=None,
                mode='shell',
                working_directory=None,
                instance=None,
                shell=None,
                slot=None):
    # Validate Linux App
    webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not webapp:
        raise ResourceNotFoundError("Unable to find web app '{}' in resource group '{}'.".format(name, resource_group_name))

    if not is_linux_webapp(webapp):
        raise ValidationError("Site is not a Linux web app. 'az webapp exec' is only supported for Linux web apps.")

    # Validate parameters
    if mode.lower() == 'execute':
        if not command:
            raise ValidationError("Command is required for 'execute' mode.")
        if shell:
            raise ValidationError("--shell is only supported in 'shell' mode.")
    elif mode.lower() == 'shell':
        if command:
            raise ValidationError("--command is only supported in 'execute' mode.")
        if args:
            raise ValidationError("--args is only supported in 'execute' mode.")
        if working_directory:
            raise ValidationError("--working-directory is only supported in 'execute' mode.")
        if instance and (instance.lower() == 'all' or ',' in instance):
            raise ValidationError("Shell mode supports a single instance. Specify one instance, or omit to use a random one.")
        if shell and not shell.startswith('/'):
            raise ValidationError("--shell must be an absolute path (e.g. /bin/sh).")
        if shell and len(shell) > _MAX_SHELL_PATH_LENGTH:
            raise ValidationError(
                "--shell path is too long (max {} characters).".format(_MAX_SHELL_PATH_LENGTH))
    else:
        raise ValidationError("Invalid mode '{}'. Supported modes: execute, shell.".format(mode))

    # Get scm site and authorization
    scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group_name, slot)

    # Resolve target instances (shared by both modes)
    target_instances = _resolve_target_instances(cmd, resource_group_name, name, instance, slot)

    # Shell mode — single interactive session
    if mode.lower() == 'shell':
        target = target_instances[0]
        cookies = {}
        if target:
            cookies['ARRAffinity'] = target
        _start_shell_session(scm_url, headers, cookies, shell=shell)
        return None

    # Execute mode - execute command on the resolved instance(s)
    def _run_on_instance(target):
        cookies = {}
        if target is not None:
            cookies['ARRAffinity'] = target
        label = target or 'default'
        try:
            result = _execute_command_on_instance(scm_url, headers, cookies, command, args, working_directory)
            logger.warning("Instance '%s' succeeded%s", label, ": {}".format(result) if result else ".")
            return {'instance': label, 'status': 'success', 'result': result}
        except CLIError as e:
            logger.warning("Instance '%s' failed: %s", label, e)
            return {'instance': label, 'status': 'failed', 'error': str(e)}

    # Execute the command on every resolved instance, in parallel. Each task
    # returns a result dict (never raises), so one bad instance can't abort the
    # others. The POST timeout (in _execute_command_on_instance) bounds how long
    # any single thread can run, so threads are always released promptly.
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(target_instances))) as executor:
        results = list(executor.map(_run_on_instance, target_instances))

    return results if len(results) > 1 else results[0] if results else None


def _resolve_target_instances(cmd, resource_group_name, name, instance, slot):
    # Resolve --instance into a validated list of instance names.
    # - None means no instance was requested: returns [None] (the load balancer picks one).
    # - "all" returns a sorted list of every instance name.
    # - Comma-separated values (e.g. "i1,i2") returns those names, each validated to exist.
    # Raises ValidationError if "all" finds no instances, or any requested name is invalid.

    if instance is None:
        return [None]

    instance_names = set(i.name for i in list_instances(cmd, resource_group_name, name, slot=slot))

    if instance.lower() == 'all':
        if not instance_names:
            raise ValidationError("No instances found for this web app.")
        return sorted(instance_names)

    requested = [i.strip() for i in instance.split(',')]
    invalid = [i for i in requested if i not in instance_names]
    if invalid:
        raise ValidationError(
            "The following instances are not valid for this web app: {}. Valid instances: {}".format(
                ', '.join(invalid), ', '.join(sorted(instance_names))))
    return requested


# --- shell mode ---


def _start_shell_session(scm_url, headers, cookies=None, shell=None):
    import sys
    import platform
    import threading
    import time
    import websocket

    ws_url = scm_url.replace('https://', 'wss://') + '/exec/shell'
    if shell:
        import urllib.parse
        ws_url += '?shell=' + urllib.parse.quote(shell, safe='')

    cookie_str = '; '.join(f'{k}={v}' for k, v in cookies.items()) if cookies else None

    # Request Websocket connection with 30s timeout
    try:
        ws = websocket.create_connection(
            ws_url,
            header=headers,
            cookie=cookie_str,
            timeout=30
        )
    except websocket.WebSocketBadStatusException as ex:
        # The server rejected the upgrade handshake
        raise CLIError(_friendly_exec_error_message(getattr(ex, 'resp_body', None)))
    except (OSError, websocket.WebSocketException) as ex:
        raise AzureConnectionError("Could not connect to the web app: {}".format(ex))
    # The 30s timeout only guards the initial connect; clear it so the recv loop blocks indefinitely
    ws.settimeout(None)

    logger.info("Connected to %s", ws_url)
    print("Connected to the web app container.")
    print("This session ends after 3 hours of inactivity, and may also end if the "
          "container restarts or the host undergoes maintenance.")
    print("Press Ctrl+C twice to exit.\n")

    # Enable ANSI rendering on Windows consoles before the recv thread starts
    # writing server output to stdout. No-op on Unix / redirected stdout.
    vt_state = _enable_windows_vt_output()

    # Run two loops until one sets closed.
    #   1. _read_from_server: server output -> stdout
    #   2. _send_to_server  : stdin -> server
    closed = threading.Event()

    def _read_from_server():
        try:
            while not closed.is_set():
                opcode, data = ws.recv_data()
                # Stop on a close frame; only render real shell output (text/binary).
                # Control frames (close/ping/pong) carry non-output payloads we must not print.
                if opcode == websocket.ABNF.OPCODE_CLOSE:
                    break
                if opcode not in (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY):
                    continue
                text = data.decode('utf-8', errors='replace')
                sys.stdout.write(text)
                sys.stdout.flush()
        except (websocket.WebSocketConnectionClosedException, OSError):
            pass
        finally:
            closed.set()

    recv_thread = threading.Thread(target=_read_from_server, daemon=True)
    recv_thread.start()

    # Tell the server our starting terminal size so the remote PTY matches.
    _send_terminal_resize(ws)

    # stdin -> server
    if platform.system() == 'Windows':
        _send_to_server_windows(ws, closed)
    else:
        _send_to_server_non_windows(ws, closed)

    closed.set()
    # Restore the original Windows console output mode, if we changed it.
    if vt_state is not None:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(vt_state[0], vt_state[1])
    try:
        ws.close()
    except Exception:  # pylint: disable=broad-except
        pass


def _enable_windows_vt_output():
    # Enable ANSI escape processing on the Windows stdout console.
    # Server output contains ANSI escape sequences (colors, cursor movement from
    # vim/top/htop). Modern Windows Terminal renders these by default, but classic
    # conhost/cmd.exe shows them as raw codes unless ENABLE_VIRTUAL_TERMINAL_PROCESSING
    # is set. Returns (handle, old_mode) so the caller can restore the original mode,
    # or None when not applicable (non-Windows, or stdout is redirected/not a console).
    import platform
    if platform.system() != 'Windows':
        return None
    import ctypes
    kernel32 = ctypes.windll.kernel32
    stdout_handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    old_mode = ctypes.c_uint32()
    # GetConsoleMode returns 0 when stdout isn't a real console (e.g. redirected to a file).
    if not kernel32.GetConsoleMode(stdout_handle, ctypes.byref(old_mode)):
        return None
    kernel32.SetConsoleMode(stdout_handle, old_mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    return stdout_handle, old_mode.value


def _send_terminal_resize(ws):
    # Send the current terminal size to the server as a JSON text frame.
    import os
    import json
    import websocket
    try:
        size = os.get_terminal_size()
        ws.send(json.dumps({"width": size.columns, "height": size.lines}))
    except (OSError, websocket.WebSocketConnectionClosedException):
        # No console attached (stdout redirected) or the session is already gone.
        pass


def _send_to_server_windows(ws, closed):
    import os
    import time
    import ctypes
    import msvcrt
    import websocket as ws_module

    # Windows normally intercepts Ctrl+C as a local interrupt. Clear ENABLE_PROCESSED_INPUT
    # so it arrives at getwch() as raw '\x03' to forward to the remote shell; restore on exit.
    kernel32 = ctypes.windll.kernel32
    stdin_handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
    old_mode = ctypes.c_uint32()
    kernel32.GetConsoleMode(stdin_handle, ctypes.byref(old_mode))
    kernel32.SetConsoleMode(stdin_handle, old_mode.value & ~0x0001)  # clear ENABLE_PROCESSED_INPUT

    # Windows special key codes → ANSI escape sequences.
    # Tab, Ctrl+D, Ctrl+L etc. work via the regular else branch (sent as-is).
    # NOTE: these scan codes should be validated during live Windows testing.
    _WINDOWS_KEY_MAP = {
        72: b'\x1b[A',     # Up
        80: b'\x1b[B',     # Down
        77: b'\x1b[C',     # Right
        75: b'\x1b[D',     # Left
        71: b'\x1b[H',     # Home
        79: b'\x1b[F',     # End
        82: b'\x1b[2~',    # Insert
        83: b'\x1b[3~',    # Delete
        73: b'\x1b[5~',    # Page Up
        81: b'\x1b[6~',    # Page Down
        59: b'\x1bOP',     # F1
        60: b'\x1bOQ',     # F2
        61: b'\x1bOR',     # F3
        62: b'\x1bOS',     # F4
        63: b'\x1b[15~',   # F5
        64: b'\x1b[17~',   # F6
        65: b'\x1b[18~',   # F7
        66: b'\x1b[19~',   # F8
        67: b'\x1b[20~',   # F9
        68: b'\x1b[21~',   # F10
        133: b'\x1b[23~',  # F11
        134: b'\x1b[24~',  # F12
        115: b'\x1b[1;5D',  # Ctrl+Left
        116: b'\x1b[1;5C',  # Ctrl+Right
        141: b'\x1b[1;5A',  # Ctrl+Up
        145: b'\x1b[1;5B',  # Ctrl+Down
    }

    last_ctrl_c = 0
    # Windows has no SIGWINCH, so poll the console size ~once a second and notify
    # the server when it changes (e.g. the user maximizes the window).
    try:
        last_size = os.get_terminal_size()
    except OSError:
        last_size = None
    last_resize_check = time.time()
    try:
        while not closed.is_set():
            now = time.time()
            if now - last_resize_check >= 1.0:
                last_resize_check = now
                try:
                    current_size = os.get_terminal_size()
                except OSError:
                    current_size = None
                if current_size is not None and current_size != last_size:
                    last_size = current_size
                    _send_terminal_resize(ws)

            # msvcrt is Python's Windows console API. kbhit() is a non-blocking peek
            # (True if a key is waiting); getwch() below reads one char and blocks if
            # the buffer is empty. So if nothing's queued, nap 50ms instead of blocking.
            if not msvcrt.kbhit():
                time.sleep(0.05)
                continue

            ch = msvcrt.getwch()
            if ch == '\x03':  # Ctrl+C: twice within 2s exits the session; a single press is forwarded to the shell
                now = time.time()
                if now - last_ctrl_c < 2:
                    break
                last_ctrl_c = now
                ws.send(b'\x03', opcode=ws_module.ABNF.OPCODE_BINARY)
            elif ch == '\r':  # Enter: Windows gives CR, Unix shells expect LF
                ws.send(b'\n', opcode=ws_module.ABNF.OPCODE_BINARY)
            elif ch == '\x08':  # Backspace: Windows gives BS, Unix shells expect DEL (0x7f)
                ws.send(b'\x7f', opcode=ws_module.ABNF.OPCODE_BINARY)
            elif ch in ('\x00', '\xe0'):  # Special key prefix
                code = ord(msvcrt.getwch())
                escape = _WINDOWS_KEY_MAP.get(code)
                if escape:
                    ws.send(escape, opcode=ws_module.ABNF.OPCODE_BINARY)
            else:
                ws.send(ch.encode('utf-8'), opcode=ws_module.ABNF.OPCODE_BINARY)
    except (ws_module.WebSocketConnectionClosedException, OSError) as ex:
        logger.info("Shell session closed: %s", ex)
    finally:
        kernel32.SetConsoleMode(stdin_handle, old_mode.value)


def _send_to_server_non_windows(ws, closed):
    import sys
    import os
    import tty
    import termios
    import time
    import signal
    import select
    import threading
    import websocket as ws_module

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    last_ctrl_c = 0

    # On Unix the terminal raises SIGWINCH whenever it's resized. The handler just
    # flags an event; the actual send happens in the loop below so we never call
    # ws.send() from inside an async signal handler.
    resize_needed = threading.Event()

    def on_sigwinch(_signum, _frame):
        resize_needed.set()

    signal.signal(signal.SIGWINCH, on_sigwinch)
    try:
        tty.setraw(fd)
        while not closed.is_set():
            if resize_needed.is_set():
                resize_needed.clear()
                _send_terminal_resize(ws)

            # Use select with a short timeout so the loop wakes up regularly to
            # re-check closed.is_set(); a blocking os.read() would hang here when
            # the server ends the session until the user happened to press a key.
            ready, _, _ = select.select([fd], [], [], 0.1)
            if not ready:
                continue
            data = os.read(fd, 4096)
            if not data:
                break
            if b'\x03' in data:  # Ctrl+C (anywhere in the chunk, e.g. a paste)
                now = time.time()
                if now - last_ctrl_c < 2:
                    break
                last_ctrl_c = now
            ws.send(data, opcode=ws_module.ABNF.OPCODE_BINARY)
    except (ws_module.WebSocketConnectionClosedException, OSError) as ex:
        logger.info("Shell session closed: %s", ex)
    finally:
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# --- execute mode ---


def _execute_command_on_instance(scm_url, headers, cookies, command, args=None, working_directory=None):
    import requests

    exec_url = f"{scm_url}/exec/execute"

    body = {"Command": command}
    if args:
        body["Args"] = args
    if working_directory:
        body["WorkingDirectory"] = working_directory

    try:
        response = requests.post(
            exec_url,
            json=body,
            headers=headers,
            cookies=cookies,
            timeout=30
        )
    except requests.exceptions.RequestException as ex:
        # No HTTP response: refused/timed-out connection, DNS/TLS/proxy error, etc.
        raise AzureConnectionError("Could not connect to the web app: {}".format(ex))

    if response.status_code == 202:
        return _parse_server_message(response.text)
    raise CLIError(_friendly_exec_error_message(response.text))


# --- shared helpers ---


def _parse_server_message(body):
    # Return the server-authored message from a response body, or None if empty.
    import json
    if not body:
        return None
    text = body.decode('utf-8', errors='ignore') if isinstance(body, (bytes, bytearray)) else str(body)
    text = text.strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed.get('Message') or None
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return text


def _friendly_exec_error_message(body):
    # Prefer the server's message; fall back to a generic line for a bodyless response.
    return _parse_server_message(body) or "The request could not be completed. Please try again later."
