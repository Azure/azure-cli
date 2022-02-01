# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=import-error,unused-import

#
# Modified from tunnel.py in appservice module
#

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

from azure.cli.core._profile import Profile
from azure.cli.core.util import should_disable_connection_verify

import requests
import urllib3

from knack.util import CLIError
from knack.log import get_logger
logger = get_logger(__name__)


# pylint: disable=no-member,too-many-instance-attributes,bare-except,no-self-use
class TunnelServer:
    def __init__(self, cli_ctx, local_addr, local_port, bastion, remote_host, remote_port):
        self.local_addr = local_addr
        self.local_port = int(local_port)
        if self.local_port != 0 and not self.is_port_open():
            raise CLIError('Defined port is currently unavailable')
        self.bastion = bastion
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.client = None
        self.ws = None
        self.last_token = None
        self.node_id = None
        self.cli_ctx = cli_ctx
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

    def _get_auth_token(self):
        profile = Profile(cli_ctx=self.cli_ctx)
        # Generate an Azure token with the VSTS resource app id
        auth_token, _, _ = profile.get_raw_token()
        content = {
            'resourceId': self.remote_host,
            'protocol': 'tcptunnel',
            'workloadHostPort': self.remote_port,
            'aztoken': auth_token[1],
            'token': self.last_token,
        }
        if self.node_id:
            custom_header = {'X-Node-Id': self.node_id}
        else:
            custom_header = {}

        web_address = 'https://{}/api/tokens'.format(self.bastion.dns_name)
        response = requests.post(web_address, data=content, headers=custom_header,
                                 verify=(not should_disable_connection_verify()))
        response_json = None

        if response.content is not None:
            response_json = json.loads(response.content.decode("utf-8"))

        if response.status_code not in [200]:
            if response_json is not None and response_json["message"] is not None:
                exp = CloudError(response, error=response_json["message"])
            else:
                exp = CloudError(response)
            raise exp

        self.last_token = response_json["authToken"]
        self.node_id = response_json["nodeId"]
        return self.last_token

    def _listen(self):
        self.sock.setblocking(True)
        self.sock.listen(100)
        index = 0
        while True:
            self.client, _address = self.sock.accept()

            auth_token = self._get_auth_token()
            host = 'wss://{}/webtunnel/{}?X-Node-Id={}'.format(self.bastion.dns_name, auth_token, self.node_id)
            self.ws = create_connection(host,
                                        sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),),
                                        sslopt={'cert_reqs': ssl.CERT_NONE},
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
            self.cleanup()
            logger.info('Both debugger and websocket threads stopped...')
            logger.info('Stopped local server..')

    def _listen_to_web_socket(self, client, ws_socket, index):
        try:
            while True:
                logger.info('Waiting for websocket data, connection status: %s, index: %s', ws_socket.connected, index)
                data = ws_socket.recv()
                logger.info('Received websocket index: %s', index)
                if data:
                    # Set the response to echo back the recieved data
                    response = data
                    logger.info('Sending to debugger, index: %s', index)
                    client.send(response)
                    logger.info('Done sending to debugger, index: %s', index)
                else:
                    logger.info('Websocket close, index: %s', index)
                    break
        except Exception as ex:  # pylint: disable=broad-except
            logger.info(ex)
        finally:
            logger.info('Client disconnected!, index: %s', index)
            client.close()
            ws_socket.close()

    def _listen_to_client(self, client, ws_socket, index):
        try:
            buf = bytearray(4096)
            while True:
                logger.info('Waiting for debugger data, index: %s', index)
                nbytes = client.recv_into(buf, len(buf))
                logger.info('Received debugger data, nbytes: %s, index: %s', nbytes, index)
                if nbytes > 0:
                    responseData = buf[0:nbytes]
                    logger.info('Sending to websocket, index: %s', index)
                    ws_socket.send_binary(responseData)
                    logger.info('Done sending to websocket, index: %s', index)
                else:
                    logger.info('Client close, index: %s', index)
                    break
        except Exception as ex:  # pylint: disable=broad-except
            logger.info(ex)
        finally:
            logger.info('Client disconnected %s', index)
            client.close()
            ws_socket.close()

    def start_server(self):
        self._listen()

    def cleanup(self):
        if self.last_token:
            logger.info('Cleaning up session')

            if self.node_id:
                custom_header = {'X-Node-Id': self.node_id}
            else:
                custom_header = {}
            logger.warning(f"custom_header = {custom_header}")

            web_address = 'https://{}/api/tokens/{}'.format(self.bastion.dns_name, self.last_token)
            logger.warning(f"web_address = {web_address}")

            response = requests.delete(web_address, headers=custom_header,
                                verify=(not should_disable_connection_verify()))
            logger.warning(f"response = {response.status_code}")
            if response.status_code == 404:
                logger.warning("session already deleted")
            elif response.status_code not in [200, 204]:
                exp = CloudError(response)
                raise exp

            logger.warning("setting last_token to null")
            self.last_token = None
            logger.warning("setting node_id to null")
            self.node_id = None
        else:
            logger.debug("Nothing to clean up")

    def get_port(self):
        return self.local_port
