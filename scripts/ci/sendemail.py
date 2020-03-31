# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def main():
    print(sys.argv)
    message = Mail(
        from_email='azclibot@microsoft.com',
        to_emails='fey@microsoft.com; iamyfy@163.com',
        subject='Test results of Azure CLI dev branch',
        html_content=get_content())
    try:
        sendgrid_key = sys.argv[1]
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)


def get_content():
    """
    Write content of email
    :return:
    """
    build_id = sys.argv[2]
    repo = sys.argv[3]
    branch = sys.argv[4]
    link = 'https://dev.azure.com/azure-sdk/public/_build/results?buildId={}&view=ms.vss-test-web.build-test-results-tab'.format(build_id)
    content = 'Hi Azure CLI team,<br>Test results of Azure CLI.<br>Repository: {}<br>Branch: {}<br>{}'.format(repo, branch, link)
    return content


if __name__ == '__main__':
    main()
