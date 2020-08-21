# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os
import json
import traceback
import datetime

from sendgrid import SendGridAPIClient

import test_data

SENDGRID_KEY = sys.argv[1]
BUILD_ID = sys.argv[2]
USER_REPO = sys.argv[3]
USER_BRANCH = sys.argv[4]
USER_TARGET = sys.argv[5]
USER_LIVE = sys.argv[6]
ARTIFACT_DIR = sys.argv[7]
REQUESTED_FOR_EMAIL = sys.argv[8]
ACCOUNT_KEY = sys.argv[9]


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
    print(ACCOUNT_KEY)

    # Upload results to storage account, container
    container = ''
    try:
        print('Uploading test results to storage account...')
        container = get_container_name()
        upload_files(container)
    except Exception:
        print(traceback.format_exc())

    # Collect statistics
    testdata = test_data.TestData(ARTIFACT_DIR)
    testdata.collect()

    # Write database
    write_db()

    # Send email
    send_email(container, testdata)


def get_container_name():
    """
    Generate container name in storage account
    :return:
    """
    date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    name = date
    if USER_LIVE == '--live':
        mode = 'live'
    elif USER_LIVE == '':
        mode = 'replay'
    else:
        mode = ''
    name += mode
    # if USER_TARGET == '' and USER_REPO == 'https://github.com/Azure/azure-cli.git' and USER_BRANCH == 'dev' and USER_LIVE == '--live':
    #     name += '_archive'
    return name


def upload_files(container):
    """
    Upload html and json files to container
    :param container:
    :return:
    """
    # Create container
    cmd = 'az storage container create -n {} --account-name clitestresultstac --account-key {}'
    os.popen(cmd.format(container, ACCOUNT_KEY))

    # Upload files
    for root, dirs, files in os.walk(ARTIFACT_DIR):
        for name in files:
            if name.endswith('html') or name.endswith('json'):
                fullpath = os.path.join(root, name)
                cmd = 'az storage blob upload -f {} -c {} -n {} --account-name clitestresultstac'
                cmd = cmd.format(fullpath, container, name)
                print('Running: ' + cmd)
                os.popen(cmd)


def write_db():
    """
    Insert data to database
    :return:
    """
    pass


def send_email(container, testdata):
    print('Sending email...')
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
                "value": get_content(container, testdata)
            }
        ]
    }
    if REQUESTED_FOR_EMAIL != '':
        data['personalizations'][0]['to'].append({'email': REQUESTED_FOR_EMAIL})
    if USER_TARGET == '' and USER_REPO == 'https://github.com/Azure/azure-cli.git' and USER_BRANCH == 'dev' and USER_LIVE == '--live' and REQUESTED_FOR_EMAIL == '':
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
        traceback.print_exc()


def get_content(container, testdata):
    """
    Compose content of email
    :return:
    """
    content = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    table, th, td {
      border: 1px solid black;
      border-collapse: collapse;
    }
    </style>
    </head>
    <body>
    """

    link = 'https://dev.azure.com/azure-sdk/internal/_build/results?buildId={}&view=ms.vss-test-web.build-test-results-tab'.format(BUILD_ID)
    content += """
    <p>Hi Azure CLI team,</p>
    Here are test results of Azure CLI.<br>
    Repository: {}<br>
    Branch: {}<br>
    Link: {}<br>
    """.format(USER_REPO, USER_BRANCH, link)

    if container != '':
        content += """
        <p>
        Test results are saved to the following container.<br>
        Storage account: /subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clitestresult/providers/Microsoft.Storage/storageAccounts/clitestresultstac <br>
        Container: {}
        </p>
        """.format(container)

    table = """
    <p>Test results summary</p>
    <table>
      <tr>
        <th>Module</th>
        <th>Passed</th>
        <th>Failed</th>
        <th>Pass rate</th>
      </tr>
    """

    for module, passed, failed, rate in testdata.modules:
        table += """
          <tr>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
          </tr>
        """.format(module, passed, failed, rate)

    table += """
      <tr>
        <td>Total</td>
        <td>{}</td>
        <td>{}</td>
        <td>{}</td>
      </tr>
    </table>
    """.format(testdata.total[1], testdata.total[2], testdata.total[3])

    content += table

    content += """
    </body>
    </html>
    """

    print(content)
    return content


if __name__ == '__main__':
    main()
