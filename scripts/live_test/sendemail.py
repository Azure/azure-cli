# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from sendgrid import SendGridAPIClient

SENDGRID_KEY = sys.argv[1]
BUILD_ID = sys.argv[2]
USER_REPO = sys.argv[3]
USER_BRANCH = sys.argv[4]
USER_TARGET = sys.argv[5]
USER_LIVE = sys.argv[6]
ARTIFACT_DIR = sys.argv[7]
REQUESTED_FOR_EMAIL = sys.argv[8]


def main():
    print(sys.argv)
    print(SENDGRID_KEY)
    print(BUILD_ID)
    print(USER_REPO)
    print(USER_BRANCH)
    print(USER_TARGET)
    print(USER_LIVE)
    print(ARTIFACT_DIR)
    print(REQUESTED_FOR_EMAIL)

    # message = Mail(
    #     from_email='azclibot@microsoft.com',
    #     to_emails='AzPyCLI@microsoft.com',
    #     subject='Test results of Azure CLI',
    #     html_content=get_content())
    data = {
        "personalizations": [
            {
                "to": [],
                "subject": "Test results of Azure CLI"
            }
        ],
        "from": {
            "email": "azclibot@microsoft.com"
        },
        "content": [
            {
                "type": "text/html",
                "value": get_content()
            }
        ]
    }
    if REQUESTED_FOR_EMAIL != '':
        data['personalizations'][0]['to'].append({'email': REQUESTED_FOR_EMAIL})
    if USER_TARGET == '' and USER_REPO == 'https://github.com/Azure/azure-cli.git' and USER_LIVE == '--live':
        data['personalizations'][0]['to'].append({'email': 'AzPyCLI@microsoft.com'})
    print(data)
    try:
        sendgrid_key = sys.argv[1]
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(data)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)


def get_content():
    """
    Compose content of email
    :return:
    """
    link = 'https://dev.azure.com/azure-sdk/internal/_build/results?buildId={}&view=ms.vss-test-web.build-test-results-tab'.format(BUILD_ID)
    content = 'Hi Azure CLI team,<br>Test results of Azure CLI.<br>Repository: {}<br>Branch: {}<br>Link: {}'.format(USER_REPO, USER_BRANCH, link)
    return content


if __name__ == '__main__':
    main()
