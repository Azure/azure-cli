# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import generate_index
import logging
import os
import random
import string
import sys
import test_data
import traceback

logger = logging.getLogger(__name__)

SENDGRID_KEY = sys.argv[1]
BUILD_ID = sys.argv[2]
USER_REPO = sys.argv[3]
USER_BRANCH = sys.argv[4]
USER_TARGET = sys.argv[5]
USER_LIVE = sys.argv[6]
ARTIFACT_DIR = sys.argv[7]
REQUESTED_FOR_EMAIL = sys.argv[8]
ACCOUNT_KEY = sys.argv[9]
COMMIT_ID = sys.argv[10]
DB_PWD = sys.argv[11]
DB_USER = sys.argv[12]
DB_HOST = sys.argv[13]
DB_PORT = sys.argv[14]
DB_SCHEME = sys.argv[15]


def main():
    logger.warning('Enter main()')

    logger.warning(sys.argv)
    logger.warning(SENDGRID_KEY)
    logger.warning(BUILD_ID)
    logger.warning(USER_REPO)
    logger.warning(USER_BRANCH)
    logger.warning(USER_TARGET)
    logger.warning(USER_LIVE)
    logger.warning(ARTIFACT_DIR)
    logger.warning(REQUESTED_FOR_EMAIL)
    logger.warning(ACCOUNT_KEY)
    logger.warning(COMMIT_ID)
    logger.warning(DB_PWD)

    # Upload results to storage account, container
    container = ''
    try:
        logger.warning('Uploading test results to storage account...')
        container = get_container_name()
        upload_files(container)
    except Exception:
        logger.exception(traceback.format_exc())

    # Collect statistics
    testdata = test_data.TestData(ARTIFACT_DIR)
    testdata.collect()

    # Generate index.html, send email
    try:
        # Generate index.html
        container_url = 'https://clitestresultstac.blob.core.windows.net/' + container
        html_content = generate_index.generate(container, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE, USER_TARGET)
        # Send email
        send_email(html_content)
    except Exception:
        logger.exception(traceback.format_exc())

    # Write database
    # try:
    #     write_db(container, testdata)
    # except Exception:
    #     logger.exception(traceback.format_exc())

    logger.warning('Exit main()')


def get_container_name():
    """
    Generate container name in storage account. It is also an identifier of the pipeline run.
    :return:
    """
    logger.warning('Enter get_container_name()')
    time = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    random_id = ''.join(random.choice(string.digits) for _ in range(6))
    name = time + '-' + random_id
    logger.warning('Exit get_container_name()')
    return name


def upload_files(container):
    """
    Upload html and json files to container
    :param container:
    :return:
    """
    logger.warning('Enter upload_files()')

    # Create container
    cmd = 'az storage container create -n {} --account-name clitestresultstac --account-key {} --public-access container'.format(container, ACCOUNT_KEY)
    os.system(cmd)

    # Upload files
    for root, dirs, files in os.walk(ARTIFACT_DIR):
        for name in files:
            if name.endswith('html') or name.endswith('json'):
                fullpath = os.path.join(root, name)
                cmd = 'az storage blob upload -f {} -c {} -n {} --account-name clitestresultstac'
                cmd = cmd.format(fullpath, container, name)
                logger.warning('Running: ' + cmd)
                os.system(cmd)

    logger.warning('Exit upload_files()')


def write_db(container, testdata):
    """
    Insert data to database.
    Sql statements to create table:
    USE clidb;
    CREATE TABLE `t1` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `repr` varchar(30) DEFAULT NULL COMMENT 'date_time_random6digits',
      `repo` varchar(200) DEFAULT NULL COMMENT 'Repo URL',
      `branch` varchar(200) DEFAULT NULL COMMENT 'Branch name',
      `commit` varchar(50) DEFAULT NULL COMMENT 'Commit ID',
      `target` varchar(2000) DEFAULT NULL COMMENT 'Target modules to test. Splited by space, Empty string represents all modules',
      `live` tinyint(1) DEFAULT NULL COMMENT 'Live run or not',
      `user` varchar(50) DEFAULT NULL COMMENT 'User (email address) who triggers the run',
      `pass` int(11) DEFAULT NULL COMMENT 'Number of passed tests',
      `fail` int(11) DEFAULT NULL COMMENT 'Number of failed tests',
      `rate` varchar(50) DEFAULT NULL COMMENT 'Pass rate',
      `detail` varchar(10000) DEFAULT NULL COMMENT 'Detail',
      `container` varchar(200) DEFAULT NULL COMMENT 'Container URL',
      `date` varchar(10) DEFAULT NULL COMMENT 'Date. E.g. 20200801',
      `time` varchar(10) DEFAULT NULL COMMENT 'Time. E.g. 183000',
      PRIMARY KEY (`id`),
      UNIQUE KEY `repr` (`repr`)
    );
    """
    logger.warning('Enter write_db()')
    logger.warning('container {}'.format(container))
    logger.warning('testdata {}'.format(testdata))
    import mysql.connector
    logger.warning('Connect DB...')
    # Connect
    cnx = mysql.connector.connect(user=DB_USER,
                                  password=DB_PWD,
                                  host=DB_HOST,
                                  port=DB_PORT,
                                  database=DB_SCHEME,
                                  connection_timeout=30)
    logger.warning('Connect DB Success')
    cursor = cnx.cursor()
    sql = 'INSERT INTO t1 (repr, repo, branch, commit, target, live, user, pass, fail, rate, detail, container, date, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
    logger.warning(sql)
    repr = container
    repo = USER_REPO
    branch = USER_BRANCH
    commit = COMMIT_ID
    target = USER_TARGET
    live = 1 if USER_LIVE == '--live' else 0
    user = REQUESTED_FOR_EMAIL
    pass0 = testdata.total[1]
    fail = testdata.total[2]
    rate = testdata.total[3]
    detail = str(testdata.modules)
    container_url = 'https://clitestresultstac.blob.core.windows.net/{}/index.html'.format(container)
    terms = container.split('-')
    date = terms[0]
    time = terms[1]
    data = (repr, repo, branch, commit, target, live, user, pass0, fail, rate, detail, container_url, date, time)
    logger.warning(data)
    cursor.execute(sql, data)

    # Make sure data is committed to the database
    cnx.commit()

    # Insert into t2
    sql = 'SELECT id FROM t1 WHERE repr = %s'
    cursor.execute(sql, (repr,))
    id0 = None
    for value in cursor:
        id0 = value[0]
    if id0:
        for module, passed, failed, rate in testdata.modules:
            sql = 'INSERT INTO t2 (module, pass, fail, rate, ref_id) VALUES (%s, %s, %s, %s, %s)'
            data = (module, passed, failed, rate, id0)
            logger.warning(sql)
            logger.warning(data)
            cursor.execute(sql, data)
        cnx.commit()

    # Close
    cursor.close()
    cnx.close()

    logger.warning('Exit write_db()')


# def send_email(html_content):
#     logger.warning('Enter send_email()')
#     from sendgrid import SendGridAPIClient
#     logger.warning('Sending email...')
#
#     data = {
#         "personalizations": [
#             {
#                 "to": [],
#                 "subject": "Test results of Azure CLI"
#             }
#         ],
#         "from": {
#             "email": "azclibot@microsoft.com"
#         },
#         "content": [
#             {
#                 "type": "text/html",
#                 "value": html_content
#             }
#         ]
#     }
#
#     if REQUESTED_FOR_EMAIL != '':
#         data['personalizations'][0]['to'].append({'email': REQUESTED_FOR_EMAIL})
#     if USER_TARGET == '' and USER_REPO == 'https://github.com/Azure/azure-cli.git' and USER_BRANCH == 'dev' and USER_LIVE == '--live' and REQUESTED_FOR_EMAIL == '':
#         data['personalizations'][0]['to'].append({'email': 'AzPyCLI@microsoft.com'})
#         data['personalizations'][0]['to'].append({'email': 'antcliTest@microsoft.com'})
#     logger.warning(data)
#
#     sendgrid_key = sys.argv[1]
#     sg = SendGridAPIClient(sendgrid_key)
#     response = sg.send(data)
#     logger.warning(response.status_code)
#     logger.warning(response.body)
#     logger.warning(response.headers)
#     logger.warning('Exit send_email()')


def send_email(html_content):
    logger.warning('Sending email...')
    from azure.communication.email import EmailClient, EmailAddress, EmailContent, EmailMessage, EmailRecipients

    client = EmailClient.from_connection_string(SENDGRID_KEY);
    content = EmailContent(
        subject="Test results of Azure CLI",
        html=html_content,
    )

    recipients = ''

    if REQUESTED_FOR_EMAIL != '':
        recipients = EmailRecipients(
            to=[
                EmailAddress(email=REQUESTED_FOR_EMAIL),
            ]
        )
    # TODO: USER_TARGET == 'all'
    elif USER_TARGET == '' and USER_REPO == 'https://github.com/Azure/azure-cli.git' and USER_BRANCH == 'dev' and USER_LIVE == '--live' and REQUESTED_FOR_EMAIL == '':
        recipients = EmailRecipients(
            to=[
                EmailAddress(email="AzPyCLI@microsoft.com"),
                EmailAddress(email="antcliTest@microsoft.com"),
            ]
        )

    if recipients:
        message = EmailMessage(sender="DoNotReply@561634e2-1674-4377-9975-10a9197437d7.azurecomm.net",
                               content=content,
                               recipients=recipients)

        response = client.send(message)
        status = client.get_send_status(response.message_id)
        print(status)
        logger.warning('Finish sending email')
    else:
        logger.warning('No recipients, skip sending email')


def get_content(container, testdata):
    """
    Compose content of email
    :return:
    """
    logger.warning('Enter get_content()')

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
    <p>[Please move this mail to normal folder if it is in junk box, otherwise, the HTML and CSS content may not be displayed correctly]</p>
    <p>
    Here are test results of Azure CLI.<br>
    Repository: {}<br>
    Branch: {}<br>
    Link: {}
    </p>
    """.format(USER_REPO, USER_BRANCH, link)

    content += """
    <p>
    <b>User Manual of Live Test Pipeline</b><br>
    <a href=https://microsoft-my.sharepoint.com/:w:/p/fey/EZGC9LwrN3RAscVS5ylG4HMBX9h7W0ZSA7CDrhXN5Lvx6g?e=V8HUmd>Word</a>  
    <a href=https://microsoft.sharepoint.com/teams/IoTToolingTeam/_layouts/OneNote.aspx?id=%2Fteams%2FIoTToolingTeam%2FShared%20Documents%2FAzure%20Management%20Experience%2FAzure%20Management%20Experience&wd=target%28AZ%20CLI%2FKnowledge%20base.one%7C18BC64EE-9328-497D-804E-6436006CA9A5%2FUser%20Manual%20of%20Live%20Test%20Pipeline%7C243EFA3E-FC7F-4612-9DA5-8E6BB2A11BD3%2F%29>OneNote</a>
    </p>
    """

    if container != '':
        content += """
        <p>
        <b>Test results location</b><br>
        Storage account: /subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clitestresult/providers/Microsoft.Storage/storageAccounts/clitestresultstac <br>
        Container: {}
        </p>
        """.format(container)

    table = """
    <p><b>Test results summary</b></p>
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

    logger.warning(content)
    logger.warning('Exit get_content()')
    return content


if __name__ == '__main__':
    main()
