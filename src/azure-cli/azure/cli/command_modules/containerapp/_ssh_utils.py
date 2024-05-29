# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=logging-fstring-interpolation

import sys
import time
import threading
import urllib
import requests
import websocket

from knack.log import get_logger
from azure.cli.core.azclierror import CLIInternalError, ValidationError
from azure.cli.core.commands.client_factory import get_subscription_id

from ._clients import ContainerAppClient
from ._utils import safe_get, is_platform_windows

# pylint: disable=import-error,ungrouped-imports
if is_platform_windows():
    import msvcrt
    from azure.cli.command_modules.container._vt_helper import (enable_vt_mode, _get_conout_mode,
                                                                _set_conout_mode, _get_conin_mode, _set_conin_mode)

logger = get_logger(__name__)

# SSH control byte values for container app proxy
SSH_PROXY_FORWARD = 0
SSH_PROXY_INFO = 1
SSH_PROXY_ERROR = 2

# SSH control byte values for container app cluster
SSH_CLUSTER_STDIN = 0
SSH_CLUSTER_STDOUT = 1
SSH_CLUSTER_STDERR = 2

# forward byte + stdin byte
SSH_INPUT_PREFIX = b"\x00\x00"

# forward byte + terminal resize byte
SSH_TERM_RESIZE_PREFIX = b"\x00\x04"

SSH_DEFAULT_ENCODING = "utf-8"
SSH_BACKUP_ENCODING = "latin_1"

SSH_CTRL_C_MSG = b"\x00\x00\x03"


class WebSocketConnection:
    def __init__(self, cmd, resource_group_name, name, revision, replica, container, startup_command):
        token_response = ContainerAppClient.get_auth_token(cmd, resource_group_name, name)
        self._token = token_response["properties"]["token"]
        self._logstream_endpoint = self._get_logstream_endpoint(cmd, resource_group_name, name,
                                                                revision, replica, container)
        self._url = self._get_url(cmd=cmd, resource_group_name=resource_group_name, name=name, revision=revision,
                                  replica=replica, container=container, startup_command=startup_command)
        self._socket = websocket.WebSocket(enable_multithread=True)
        logger.info("Attempting to connect to %s", self._url)
        self._socket.connect(self._url, header=[f"Authorization: Bearer {self._token}"])

        self.is_connected = True
        self._windows_conout_mode = None
        self._windows_conin_mode = None
        if is_platform_windows():
            self._windows_conout_mode = _get_conout_mode()
            self._windows_conin_mode = _get_conin_mode()

    @classmethod
    def _get_logstream_endpoint(cls, cmd, resource_group_name, name, revision, replica, container):
        containers = ContainerAppClient.get_replica(cmd,
                                                    resource_group_name,
                                                    name, revision, replica)["properties"]["containers"]
        container_info = [c for c in containers if c["name"] == container]
        if not container_info:
            raise ValidationError(f"No such container: {container}")
        return container_info[0]["logStreamEndpoint"]

    def _get_url(self, cmd, resource_group_name, name, revision, replica, container, startup_command):
        sub = get_subscription_id(cmd.cli_ctx)
        base_url = self._logstream_endpoint
        proxy_api_url = base_url[:base_url.index("/subscriptions/")].replace("https://", "")
        encoded_cmd = urllib.parse.quote_plus(startup_command)

        return (f"wss://{proxy_api_url}/subscriptions/{sub}/resourceGroups/{resource_group_name}/containerApps/{name}"
                f"/revisions/{revision}/replicas/{replica}/containers/{container}/exec"
                f"?command={encoded_cmd}")

    def disconnect(self):
        logger.warning("Disconnecting...")
        self.is_connected = False
        self._socket.close()
        if self._windows_conout_mode and self._windows_conin_mode:
            _set_conout_mode(self._windows_conout_mode)
            _set_conin_mode(self._windows_conin_mode)

    def send(self, *args, **kwargs):
        return self._socket.send(*args, **kwargs)

    def recv(self, *args, **kwargs):
        return self._socket.recv(*args, **kwargs)


def _decode_and_output_to_terminal(connection: WebSocketConnection, response, encodings):
    for i, encoding in enumerate(encodings):
        try:
            print(response[2:].decode(encoding), end="", flush=True)
            break
        except UnicodeDecodeError as e:
            if i == len(encodings) - 1:  # ran out of encodings to try
                connection.disconnect()
                logger.info("Proxy Control Byte: %s", response[0])
                logger.info("Cluster Control Byte: %s", response[1])
                logger.info("Hexdump: %s", response[2:].hex())
                raise CLIInternalError("Failed to decode server data") from e
            logger.info("Failed to encode with encoding %s", encoding)


def read_ssh(connection: WebSocketConnection, response_encodings):
    # We just need to do resize once for the whole session
    _resize_terminal(connection)

    # response_encodings is the ordered list of Unicode encodings to try to decode with before raising an exception
    while connection.is_connected:
        response = connection.recv()
        if not response:
            connection.disconnect()
        else:
            logger.info("Received raw response %s", response.hex())
            proxy_status = response[0]
            if proxy_status == SSH_PROXY_INFO:
                print(f"INFO: {response[1:].decode(SSH_DEFAULT_ENCODING)}")
            elif proxy_status == SSH_PROXY_ERROR:
                print(f"ERROR: {response[1:].decode(SSH_DEFAULT_ENCODING)}")
            elif proxy_status == SSH_PROXY_FORWARD:
                control_byte = response[1]
                if control_byte in (SSH_CLUSTER_STDOUT, SSH_CLUSTER_STDERR):
                    _decode_and_output_to_terminal(connection, response, response_encodings)
                else:
                    connection.disconnect()
                    raise CLIInternalError("Unexpected message received")


def _send_stdin(connection: WebSocketConnection, getch_fn):
    while connection.is_connected:
        ch = getch_fn()
        if connection.is_connected:
            connection.send(b"".join([SSH_INPUT_PREFIX, ch]))


def _resize_terminal(connection: WebSocketConnection):
    from shutil import get_terminal_size
    size = get_terminal_size()
    if connection.is_connected:
        connection.send(b"".join([SSH_TERM_RESIZE_PREFIX,
                                  f'{{"Width": {size.columns}, '
                                  f'"Height": {size.lines}}}'.encode(SSH_DEFAULT_ENCODING)]))


def _getch_unix():
    return sys.stdin.read(1).encode(SSH_DEFAULT_ENCODING)


def _getch_windows():
    while not msvcrt.kbhit():
        time.sleep(0.01)
    return msvcrt.getch()


def ping_container_app(app):
    site = safe_get(app, "properties", "configuration", "ingress", "fqdn")
    if site:
        try:
            resp = requests.get(f'https://{site}', timeout=30)
            if not resp.ok:
                logger.info(f"Got bad status pinging app: {resp.status_code}")
        except requests.exceptions.ReadTimeout:
            logger.info("Timed out while pinging app external URL")
    else:
        logger.info("Could not fetch site external URL")


def get_stdin_writer(connection: WebSocketConnection):
    if not is_platform_windows():
        import tty
        tty.setcbreak(sys.stdin.fileno())  # needed to prevent printing arrow key characters
        writer = threading.Thread(target=_send_stdin, args=(connection, _getch_unix))
    else:
        enable_vt_mode()  # needed for interactive commands (ie vim)
        writer = threading.Thread(target=_send_stdin, args=(connection, _getch_windows))

    return writer
