# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests


class DirectLineClient(object):
    """Shared methods for the parsed result objects."""

    def __init__(self, direct_line_secret):
        self._direct_line_secret = direct_line_secret
        self._base_url = 'https://directline.botframework.com/v3/directline'
        self.__set_headers()
        self.__start_conversation()
        self._watermark = ''

    def send_message(self, text):
        """Send raw text to bot framework using direct line api"""
        url = '/'.join([self._base_url, 'conversations', self._conversationid, 'activities'])
        json_payload = {
            'conversationId': self._conversationid,
            'type': 'message',
            'from': {'id': 'user1'},
            'text': text
        }
        bot_response = requests.post(url, headers=self._headers, json=json_payload)
        return bot_response

    def get_message(self):
        """Get a response message back from the bot framework using direct line api"""
        url = '/'.join([self._base_url, 'conversations', self._conversationid, 'activities'])
        url = url + '?watermark=' + self._watermark
        bot_response = requests.get(url, headers=self._headers,
                                   json={'conversationId': self._conversationid})
        if bot_response.status_code == 200:
            json_response = bot_response.json()

            if 'watermark' in json_response:
                self._watermark = json_response['watermark']

            if 'activities' in json_response:
                activities_count = len(json_response['activities'])
                if activities_count > 0:
                    return bot_response, json_response['activities'][activities_count - 1]['text']
                else:
                    return bot_response, "No new messages"
        return bot_response, "error contacting bot for response"

    def __set_headers(self):
        headers = {'Content-Type': 'application/json'}
        value = ' '.join(['Bearer', self._direct_line_secret])
        headers.update({'Authorization': value})
        self._headers = headers

    def __start_conversation(self):

        # Start conversation and get us a conversationId to use
        url = '/'.join([self._base_url, 'conversations'])
        botresponse = requests.post(url, headers=self._headers)

        # Extract the conversationID for sending messages to bot
        jsonresponse = botresponse.json()
        self._conversationid = jsonresponse['conversationId']