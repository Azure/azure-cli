# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=import-error,unused-import
import sys
import ssl
import json
import socket
import time
import traceback
import logging as logs
from contextlib import closing
from datetime import datetime
from threading import Thread

import websocket
from websocket import create_connection, WebSocket

from knack.util import CLIError
from knack.log import get_logger
logger = get_logger(__name__)


class TunnelWebSocket(WebSocket):
    def recv_frame(self):
        frame = super(TunnelWebSocket, self).recv_frame()
        logger.info('Received frame: %s', frame)
        return frame

    def recv(self):
        data = super(TunnelWebSocket, self).recv()
        logger.info('Received websocket data: %s', data)
        return data


# pylint: disable=no-member,too-many-instance-attributes,bare-except,no-self-use
class TunnelServer:
    def __init__(self, local_addr, local_port, remote_addr, remote_user_name, remote_password, instance):
        self.local_addr = local_addr
        self.local_port = local_port
        if self.local_port != 0 and not self.is_port_open():
            raise CLIError('Defined port is currently unavailable')
        if remote_addr.startswith("https://"):
            self.remote_addr = remote_addr[8:]
        else:
            self.remote_addr = remote_addr
        self.remote_user_name = remote_user_name
        self.remote_password = remote_password
        self.instance = instance
        self.client = None
        self.ws = None
        logger.info('Creating a socket on port: %s', self.local_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.info('Setting socket options')
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        logger.info('Binding to socket on local address and port')
        self.sock.bind((self.local_addr, self.local_port))
        if self.local_port == 0:
            self.local_port = self.sock.getsockname()[1]
            logger.info('Auto-selecting port: %s', self.local_port)
        logger.info('Finished initialization')

    def create_basic_auth(self):
        from base64 import b64encode
        basic_auth_string = '{}:{}'.format(self.remote_user_name, self.remote_password).encode()
        basic_auth_string = b64encode(basic_auth_string).decode('utf-8')
        return basic_auth_string

    def is_port_open(self):
        is_port_open = False
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex(('', self.local_port)) == 0:
                logger.info('Port %s is NOT open', self.local_port)
            else:
                logger.info('Port %s is open', self.local_port)
                is_port_open = True
            return is_port_open

    def is_webapp_up(self):
        import certifi
        import urllib3
        from azure.cli.core.util import should_disable_connection_verify

        try:
            import urllib3.contrib.pyopenssl
            urllib3.contrib.pyopenssl.inject_into_urllib3()
        except ImportError:
            pass

        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        if should_disable_connection_verify():
            http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        headers = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(self.remote_user_name, self.remote_password))
        url = 'https://{}{}'.format(self.remote_addr, '/AppServiceTunnel/Tunnel.ashx?GetStatus&GetStatusAPIVer=2')
        if self.instance is not None:
            headers['Cookie'] = 'ARRAffinity=' + self.instance
        r = http.request(
            'GET',
            url,
            headers=headers,
            preload_content=False
        )

        logger.warning('Verifying if app is running....')

        if r.status != 200:
            raise CLIError("Failed to connect to '{}' with status code '{}' and reason '{}'".format(
                url, r.status, r.reason))
        resp_msg = r.read().decode('utf-8')
        json_data = json.loads(resp_msg)

        if json_data.get('state', None) is None:
            return False

        if 'STARTED' in json_data["state"].upper():
            if json_data["canReachPort"] is False:
                raise CLIError(
                    'SSH is not enabled for this app. '
                    'To enable SSH follow this instructions: '
                    'https://go.microsoft.com/fwlink/?linkid=2132395')
            if json_data["canReachPort"] is True:
                logger.warning("App is running. Trying to establish tunnel connection...")
                return True
        elif 'STOPPED' in json_data["state"].upper():
            raise CLIError(
                'SSH endpoint unreachable, your app must be '
                'running before it can accept SSH connections.'
                'Use `az webapp log tail` to review the app startup logs.')
        elif 'STARTING' in json_data["state"].upper():
            logger.warning('Waiting for app to start up... ')
        return False

    def _listen(self):
        self.sock.listen(100)
        index = 0
        basic_auth_string = self.create_basic_auth()
        while True:
            self.client, _address = self.sock.accept()
            self.client.settimeout(60 * 60)
            host = 'wss://{}{}'.format(self.remote_addr, '/AppServiceTunnel/Tunnel.ashx')
            basic_auth_header = ['Authorization: Basic {}'.format(basic_auth_string)]
            if self.instance is not None:
                basic_auth_header.append('Cookie: ARRAffinity=' + self.instance)
            cli_logger = get_logger()  # get CLI logger which has the level set through command lines
            is_verbose = any(handler.level <= logs.INFO for handler in cli_logger.handlers)
            if is_verbose:
                logger.info('Websocket tracing enabled')
                websocket.enableTrace(True)
            else:
                logger.info('Websocket tracing disabled, use --verbose flag to enable')
                websocket.enableTrace(False)
            self.ws = create_connection(host,
                                        sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),),
                                        class_=TunnelWebSocket,
                                        header=basic_auth_header,
                                        sslopt={'cert_reqs': ssl.CERT_NONE},
                                        timeout=60 * 60,
                                        enable_multithread=True)
            logger.info('Websocket, connected status: %s', self.ws.connected)
            index = index + 1
            logger.info('Got debugger connection... index: %s', index)
            debugger_thread = Thread(target=self._listen_to_client, args=(self.client, self.ws, index))
            web_socket_thread = Thread(target=self._listen_to_web_socket, args=(self.client, self.ws, index))
            debugger_thread.start()
            web_socket_thread.start()
            logger.info('Both debugger and websocket threads started...')
            logger.info('Successfully connected to local server..')
            debugger_thread.join()
            web_socket_thread.join()
            logger.info('Both debugger and websocket threads stopped...')
            logger.info('Stopped local server..')

    def _listen_to_web_socket(self, client, ws_socket, index):
        try:
            while True:
                logger.info('Waiting for websocket data, connection status: %s, index: %s', ws_socket.connected, index)
                data = ws_socket.recv()
                logger.info('Received websocket data: %s, index: %s', data, index)
                if data:
                    # Set the response to echo back the recieved data
                    response = data
                    logger.info('Sending to debugger, response: %s, index: %s', response, index)
                    client.sendall(response)
                    logger.info('Done sending to debugger, index: %s', index)
                else:
                    break
        except Exception as ex:  # pylint: disable=broad-except
            logger.info(ex)
        finally:
            logger.info('Client disconnected!, index: %s', index)
            client.close()
            ws_socket.close()

    def _listen_to_client(self, client, ws_socket, index):
        try:
            while True:
                logger.info('Waiting for debugger data, index: %s', index)
                buf = bytearray(4096)
                nbytes = client.recv_into(buf, 4096)
                logger.info('Received debugger data, nbytes: %s, index: %s', nbytes, index)
                if nbytes > 0:
                    responseData = buf[0:nbytes]
                    logger.info('Sending to websocket, response data: %s, index: %s', responseData, index)
                    ws_socket.send_binary(responseData)
                    logger.info('Done sending to websocket, index: %s', index)
                else:
                    break
        except Exception as ex:  # pylint: disable=broad-except
            logger.info(ex)
            logger.warning("Connection Timed Out")
        finally:
            logger.info('Client disconnected %s', index)
            client.close()
            ws_socket.close()

    def start_server(self):
        self._listen()

    def get_port(self):
        return self.local_port
