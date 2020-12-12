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

from msrestazure.azure_exceptions import CloudError
from azure.cli.core.util import should_disable_connection_verify

import requests
import urllib3

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
    def __init__(self, local_addr, local_port, bastion_address, remote_host, remote_port):
        self.local_addr = local_addr
        self.local_port = int(local_port)
        if self.local_port != 0 and not self.is_port_open():
            raise CLIError('Defined port is currently unavailable')
        
        self.bastion_address = bastion_address
        self.remote_host = remote_host
        self.remote_port = remote_port
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

    def is_port_open(self):
        is_port_open = False
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex(('', self.local_port)) == 0:
                logger.info('Port %s is NOT open', self.local_port)
            else:
                logger.info('Port %s is open', self.local_port)
                is_port_open = True
            return is_port_open

    def _listen(self):
        self.sock.listen(100)
        index = 0
        while True:
            self.client, _address = self.sock.accept()
            self.client.settimeout(60 * 60)


            content = {
                'resourceId': self.remote_host,
                'protocol': 'tcptunnel',
                'hostport': self.remote_port,
                'aztoken': ''
            }

            web_address = 'https://{}/api/tokens'.format(self.bastion_address)
            response = requests.post(web_address, data=content, verify=(not should_disable_connection_verify()))

            if response.status_code not in [200]:
                exp = CloudError(response)
                raise exp


            auth_token = response.content.decode("utf-8")["authToken"]
            host = 'wss://{}/webtunnel/{}'.format(self.bastion_address, auth_token)
            
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
