# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core.azclierror import ResourceNotFoundError, ValidationError, AzureConnectionError, CLIInternalError

from ._appservice_utils import _generic_site_operation
from .custom import _get_scm_url, get_scm_site_headers, list_instances
from .utils import is_linux_webapp

logger = get_logger(__name__)

_MAX_SHELL_PATH_LENGTH = 256

# Windows special key codes and ANSI escape sequences.
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
        raise ResourceNotFoundError(
            "Unable to find web app '{}' in resource group '{}'.".format(name, resource_group_name))

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
            raise ValidationError(
                "Shell mode supports a single instance. Specify one instance, or omit to use a random one.")
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

    # Execute mode - run the command on each resolved instance in parallel.
    args_list = [(target, scm_url, headers, command, args, working_directory) for target in target_instances]
    results = _execute_in_parallel(_run_execute_on_instance, args_list)

    return results


def _resolve_target_instances(cmd, resource_group_name, name, instance, slot):
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


def _run_execute_on_instance(target, scm_url, headers, command, args, working_directory):
    # Run the command on a single instance and return a result dict. Never raises:
    # a CLIError from one instance is captured so it can't abort the others.
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


def _execute_in_parallel(fn, args_list, max_workers=10):
    # Run fn(*args) for each arg tuple on a thread pool
    import concurrent.futures
    max_workers = min(max_workers, len(args_list))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fn, *args) for args in args_list]
        return [f.result() for f in futures]


# --- shell mode ---


def _start_shell_session(scm_url, headers, cookies=None, shell=None):
    import codecs
    import platform
    import threading
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
        raise CLIInternalError(_friendly_exec_error_message(getattr(ex, 'resp_body', None)))
    except (OSError, websocket.WebSocketException) as ex:
        raise AzureConnectionError("Could not connect to the web app: {}".format(ex))

    # Clear the 30s connect timeout so the read_from_server loop blocks indefinitely
    ws.settimeout(None)

    logger.info("Connected to %s", ws_url)
    print("Connected to the web app container.")
    print("This session ends after 3 hours of inactivity, and may also end if the "
          "container restarts or the host undergoes maintenance.")
    print("Press Ctrl+C twice to exit.\n")

    # Enable ANSI rendering on Windows consoles. No-op on Unix / redirected stdout.
    vt_state = _enable_windows_vt_output()

    # Incremental UTF-8 decoder: a multi-byte char can split across frames, so it buffers the
    # partial bytes until the next frame completes them. Replace invalid char as a fallback.
    decoder = codecs.getincrementaldecoder('utf-8')('replace')

    # Run two loops until one sets closed.
    #   1. _read_from_server: server output -> stdout
    #   2. _send_to_server  : stdin -> server
    closed = threading.Event()

    # 1. server -> stdout, on a background thread
    threading.Thread(
        target=_read_from_server,
        args=(ws, closed, decoder),
        daemon=True).start()

    # Send starting terminal size so the remote PTY matches.
    _send_terminal_resize(ws)

    # 2. stdin -> server, blocks the main thread until the session ends
    if platform.system() == 'Windows':
        _send_to_server_windows(ws, closed)
    else:
        _send_to_server_non_windows(ws, closed)

    # Send loop returned: signal the read thread to stop, then clean up.
    closed.set()

    # Restore the original Windows console output mode, if changed.
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
    # is set on stdout's console mode. Returns (handle, old_mode) so the caller can restore
    # the original mode, or None when not applicable (non-Windows, or stdout is redirected/not a console).

    import platform
    if platform.system() != 'Windows':
        return None
    import ctypes
    kernel32 = ctypes.windll.kernel32

    stdout_handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    # GetConsoleMode returns 0 when stdout isn't a real console (e.g. redirected to a file).
    old_mode = ctypes.c_uint32()
    if not kernel32.GetConsoleMode(stdout_handle, ctypes.byref(old_mode)):
        return None

    # OR in the VT bit, preserving the other mode flags.
    kernel32.SetConsoleMode(stdout_handle, old_mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    return stdout_handle, old_mode.value


def _read_from_server(ws, closed, decoder):
    # Runs on a background thread: stream server output -> stdout until the socket closes.
    import sys
    import websocket
    try:
        while not closed.is_set():
            opcode, data = ws.recv_data()
            # Stop on a close frame
            if opcode == websocket.ABNF.OPCODE_CLOSE:
                break
            # Text and binary is considered shell output. Do not print non-shell output (e.g. ping/pong) to stdout.
            if opcode not in (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY):
                continue
            text = decoder.decode(data)
            sys.stdout.write(text)
            sys.stdout.flush()
    except (websocket.WebSocketConnectionClosedException, OSError):
        pass
    finally:
        closed.set()


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

    # Clear the ENABLE_PROCESSED_INPUT flag from stdin's console mode so a Ctrl+C is processed as
    # a raw byte and forwarded to the remote shell, instead of interrupting az locally; restored on exit.
    kernel32 = ctypes.windll.kernel32
    stdin_handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
    old_mode = ctypes.c_uint32()
    kernel32.GetConsoleMode(stdin_handle, ctypes.byref(old_mode))
    kernel32.SetConsoleMode(stdin_handle, old_mode.value & ~0x0001)

    last_ctrl_c = 0

    # Set up for terminal window resizing
    try:
        last_size = os.get_terminal_size()
    except OSError:
        last_size = None
    last_resize_check = time.time()

    try:
        while not closed.is_set():
            now = time.time()

            # Poll the console size every ~1s and notify the server when it changes
            if now - last_resize_check >= 1.0:
                last_resize_check = now
                try:
                    current_size = os.get_terminal_size()
                except OSError:
                    current_size = None
                if current_size is not None and current_size != last_size:
                    last_size = current_size
                    _send_terminal_resize(ws)

            # kbhit() is a non-blocking peek: returns True when a key is waiting in the console input buffer.
            # If no key is waiting, sleep 0.05 seconds
            if not msvcrt.kbhit():
                time.sleep(0.05)
                continue

            # If key is waiting: Drain every key queued right now into one buffer and send a single frame.
            buf = bytearray()
            exit_session = False
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                # If Ctrl+C twice within 2s, exit the session. Otherwise, send to server.
                if ch == '\x03':
                    now = time.time()
                    if now - last_ctrl_c < 2:
                        exit_session = True
                        break
                    last_ctrl_c = now
                    buf += b'\x03'
                elif ch == '\r':  # Enter: Windows gives CR, Unix shells expect LF
                    buf += b'\n'
                elif ch == '\x08':  # Backspace: Windows gives BS, Unix shells expect DEL (0x7f)
                    buf += b'\x7f'
                elif ch in ('\x00', '\xe0'):  # Special key prefix: the next getwch() is the key code
                    escape = _WINDOWS_KEY_MAP.get(ord(msvcrt.getwch()))
                    if escape:
                        buf += escape
                else:
                    buf += ch.encode('utf-8')

            if buf:
                ws.send(bytes(buf), opcode=ws_module.ABNF.OPCODE_BINARY)
            if exit_session:
                break
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

    # Set up for terminal window resizing
    resize_needed = threading.Event()

    def on_sigwinch(_signum, _frame):
        resize_needed.set()

    # On SIGWINCH (terminal resize), run on_sigwinch to signal resize_needed.
    # This will eventually allow send_terminal_resize to be called and send resize request to server.
    signal.signal(signal.SIGWINCH, on_sigwinch)

    try:
        # Raw mode: pass keystrokes straight to the remote shell (no local echo/buffering).
        tty.setraw(fd)
        while not closed.is_set():
            if resize_needed.is_set():
                resize_needed.clear()
                _send_terminal_resize(ws)

            # Wait for input on fd (stdin). If nothing for 0.1s, loop back to re-check if the session closed.
            ready, _, _ = select.select([fd], [], [], 0.1)
            if not ready:
                continue
            data = os.read(fd, 4096)
            if not data:
                break
            if b'\x03' in data:  # Ctrl+C
                now = time.time()
                if now - last_ctrl_c < 2:
                    break  # Ctrl+C twice in 2 seconds will end the session
                last_ctrl_c = now
            ws.send(data, opcode=ws_module.ABNF.OPCODE_BINARY)
    except (ws_module.WebSocketConnectionClosedException, OSError) as ex:
        logger.info("Shell session closed: %s", ex)
    finally:
        # Reset defaults: stop listening for resize signals, restore terminal out of raw mode.
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
    raise CLIInternalError(_friendly_exec_error_message(response.text))


# --- shared helpers ---


def _friendly_exec_error_message(body):
    return _parse_server_message(body) or "The request could not be completed. Please try again later."


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
    except ValueError:  # includes json.JSONDecodeError
        pass
    return text
