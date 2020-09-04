# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os
import traceback
import datetime
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
COMMIT_ID = sys.argv[10]
DB_PWD = sys.argv[11]


def main():
    print('Enter main()')

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
    print(COMMIT_ID)
    print(DB_PWD)

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

    # Send email
    try:
        send_email(container, testdata)
    except Exception:
        print(traceback.format_exc())

    # Write database
    try:
        write_db(container, testdata)
    except Exception:
        print(traceback.format_exc())

    print('Exit main()')


def get_container_name():
    """
    Generate container name in storage account
    :return:
    """
    print('Enter get_container_name()')

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
    print('Exit get_container_name()')
    return name


def upload_files(container):
    """
    Upload html and json files to container
    :param container:
    :return:
    """
    print('Enter upload_files()')

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

    print('Exit upload_files()')


def write_db(container, testdata):
    """
    Insert data to database.
    Sql statements to create table:
    USE clidb;
    CREATE TABLE t1 (
       repo       VARCHAR(200) COMMENT 'Repo URL',
       branch     VARCHAR(200) COMMENT 'Branch name',
       commit     VARCHAR(50) COMMENT 'Commit ID',
       target     VARCHAR(2000) COMMENT 'Target modules to test. Splited by space, Empty string represents all modules',
       live       TINYINT(1) COMMENT 'Live run or not',
       user       VARCHAR(50) COMMENT 'User (email address) who triggers the run',
       pass       INT COMMENT 'Number of passed tests',
       fail       INT COMMENT 'Number of failed tests',
       rate       VARCHAR(50) COMMENT 'Pass rate',
       detail     VARCHAR(10000) COMMENT 'Detail',
       container  VARCHAR(200) COMMENT 'Container URL',
       date       VARCHAR(10) COMMENT 'Date. E.g. 20200801',
       time       VARCHAR(10) COMMENT 'Time. E.g. 183000'
    );

    """
    print('Enter write_db()')

    import mysql.connector
    print('Writing DB...')
    # Connect
    cnx = mysql.connector.connect(user='fey@clisqldbserver',
                                  password=DB_PWD,
                                  host='clisqldbserver.mysql.database.azure.com',
                                  database='clidb')
    cursor = cnx.cursor()
    sql = 'INSERT INTO t1 (repo, branch, commit, target, live, user, pass, fail, rate, detail, container, date, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
    repo = USER_REPO
    branch = USER_BRANCH
    commit = COMMIT_ID
    target = USER_TARGET
    live = 1 if USER_LIVE == '--live' else 0
    user = REQUESTED_FOR_EMAIL
    pass0 = testdata.total[2]
    fail = testdata.total[1]
    rate = testdata.total[3]
    detail = str(testdata.modules)
    container = 'https://clitestresultstac.blob.core.windows.net/' + container
    d = datetime.datetime.now()
    date = d.strftime('%Y%m%d')
    time = d.strftime('%H%M%S')
    data = (repo, branch, commit, target, live, user, pass0, fail, rate, detail, container, date, time)
    print(data)
    cursor.execute(sql, data)

    # Make sure data is committed to the database
    cnx.commit()
    # Close
    cursor.close()
    cnx.close()

    print('Exit write_db()')


def send_email(container, testdata):
    print('Enter send_email()')

    from sendgrid import SendGridAPIClient
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

    sendgrid_key = sys.argv[1]
    sg = SendGridAPIClient(sendgrid_key)
    response = sg.send(data)
    print(response.status_code)
    print(response.body)
    print(response.headers)

    print('Exit send_email()')


def get_content(container, testdata):
    """
    Compose content of email
    :return:
    """
    print('Enter get_content()')

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

    content += """
    <p>
    User Manual of Live Test Pipeline<br>
    <a href=https://microsoft-my.sharepoint.com/:w:/p/fey/EZGC9LwrN3RAscVS5ylG4HMBX9h7W0ZSA7CDrhXN5Lvx6g?e=V8HUmd>Word</a><br> 
    <a href=https://microsoft.sharepoint.com/teams/IoTToolingTeam/_layouts/OneNote.aspx?id=%2Fteams%2FIoTToolingTeam%2FShared%20Documents%2FAzure%20Management%20Experience%2FAzure%20Management%20Experience&wd=target%28AZ%20CLI%2FKnowledge%20base.one%7C18BC64EE-9328-497D-804E-6436006CA9A5%2FUser%20Manual%20of%20Live%20Test%20Pipeline%7C243EFA3E-FC7F-4612-9DA5-8E6BB2A11BD3%2F%29>OneNote</a><br>
    </p>
    """

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
    print('Exit get_content()')
    return content


if __name__ == '__main__':
    main()
