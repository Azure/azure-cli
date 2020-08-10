# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import msal
import requests
import json

USER = False


def delegated():
    client_id = 'b1023c2f-3625-4726-a173-09449d190793'
    # client_id = 'df1f9b2a-1f75-4032-8396-2b03d4631e6b'
    # authority = 'https://login.microsoftonline.com/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a'
    # authority = 'https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47'
    authority = 'https://login.microsoftonline.com/organizations'
    username = 'azurecli@microsoft.com'
    password = ''
    scopes = []
    endpoint = 'https://graph.microsoft.com/v1.0/me/sendMail'

    app = msal.PublicClientApplication(
        client_id,
        authority=authority
    )

    result = None

    accounts = app.get_accounts(username)
    print(accounts)
    if accounts:
        logging.info("Account(s) exists in cache, probably with token too. Let's try.")
        result = app.acquire_token_silent(scopes, account=accounts[0])

    if not result:
        logging.info("No suitable token exists in cache. Let's get a new one from AAD.")
        result = app.acquire_token_by_username_password(username, password, scopes=scopes)
        # result = app.acquire_token_by_authorization_code()

    # print(result)

    if "access_token" in result:
        token = result['access_token']
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        raise Exception()

    # Get profile of me
    response = requests.get(
        'https://graph.microsoft.com/v1.0/me',
        headers={'Authorization': 'Bearer ' + token}
    )

    print(response.json())

    # Send email
    payload = {
        "message": {
            "subject": "Meet for lunch?",
            "body": {
                "contentType": "Text",
                "content": "The new cafeteria is open."
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": "fey@microsoft.com"
                    }
                }
            ]
        }
    }

    response = requests.post(
        'https://graph.microsoft.com/v1.0/me/sendMail',
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
        json=payload
    )

    print(response.json())


def main():
    delegated()
    return

    app = msal.ConfidentialClientApplication(
        'b1023c2f-3625-4726-a173-09449d190793',
        authority='https://login.microsoftonline.com/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a',
        client_credential='y5VL3nj0Yu.zYcQnra~ck-PF.6fr-t9p3u'
    )

    result = None
    scope = ['https://graph.microsoft.com/.default']

    if USER:
        accounts = app.get_accounts(username='fey@microsoft.com')
        if accounts:
            logging.info("Account(s) exists in cache, probably with token too. Let's try.")
            result = app.acquire_token_silent(scope, account=accounts[0])

        if not result:
            logging.info("No suitable token exists in cache. Let's get a new one from AAD.")

            result = app.acquire_token_by_username_password(
                'fey@microsoft', 'asdf', scope
            )
    else:
        result = app.acquire_token_silent(scope, account=None)
        if not result:
            logging.info("No suitable token exists in cache. Let's get a new one from AAD.")
            result = app.acquire_token_for_client(scope)
        # print(result)
    if "access_token" in result:
        token = result['access_token']
    else:
        raise Exception()

    # Calling graph using the access token
    # graph_data = requests.get(  # Use token to call downstream service
    #     'https://graph.microsoft.com/v1.0/users',
    #     headers={'Authorization': 'Bearer ' + token}, ).json()
    # print("Graph API call result: %s" % json.dumps(graph_data, indent=2))

    payload = {
        "message": {
            "subject": "Meet for lunch?",
            # "body": {
            #     "contentType": "Text",
            #     "content": "The new cafeteria is open."
            # },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": "jiasli@microsoft.com"
                    }
                }
            ],
            "from": {
                "emailAddress": {
                    "address": "fey@contoso.com"
                }
            }
            # "ccRecipients": [
            #     {
            #         "emailAddress": {
            #             "address": "fey@microsoft.com"
            #         }
            #     }
            # ]
        }
    }

    if USER:
        response = requests.post(
            'https://graph.microsoft.com/v1.0/me/sendMail',
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
            json=payload
        )
    else:
        response = requests.post(
            'https://graph.microsoft.com/v1.0/users/fey_microsoft.com#EXT#@AzureSDKTeam.onmicrosoft.com/sendMail',
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
            json=payload
        )
    print(response.json())


if __name__ == '__main__':
    main()
