# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Monitor test results. Create issues when dropping.

import sys
import requests

DB_PWD = sys.argv[1]
GITHUB_TOKEN = sys.argv[2]


def main():
    data, regression_data = analyze_data()
    create_issue(data, regression_data)


def analyze_data():
    import mysql.connector
    # Connect
    cnx = mysql.connector.connect(user='fey@clisqldbserver',
                                  password=DB_PWD,
                                  host='clisqldbserver.mysql.database.azure.com',
                                  database='clidb')
    cursor = cnx.cursor(buffered=True)
    sql = 'select module from t2 group by module order by module;'
    cursor.execute(sql)
    modules = []
    for value in cursor:
        if not value[0].startswith('ext-'):
            modules.append(value[0])

    print(modules)

    data = []
    regression_data = []
    for module in modules:
        sql = "select t2.module, t2.pass, t2.fail, t2.rate, t1.container, t1.date, t1.time from t1 join t2 on t1.id = t2.ref_id where t2.module = '{}' and t1.branch = 'dev' and t1.target = '' and t1.repo = 'https://github.com/Azure/azure-cli.git' and t1.live = 1 order by t1.date desc, t1.time desc limit 2;"
        cursor.execute(sql.format(module))
        new = old = None
        for value in cursor:
            data.append(value)
            if new is None:
                new = value
            else:
                old = value
        # print(new)
        # print(old)
        if new[2] > old[2] or float(new[3].strip('%')) < float(old[3].strip('%')):
            regression_data.append(new)
            regression_data.append(old)
            # print(new)
            # print(old)

    # print(data)

    return data, regression_data


def create_issue(data, regression_data):
    # Create Github issue
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    issue_body = '''
This issue is created by a program.
[Latest testing results of Azure CLI](https://clitestresultstac.blob.core.windows.net/latest/index.html)
[User Manual of Live Test Pipeline](https://microsoft-my.sharepoint.com/:w:/p/fey/EZGC9LwrN3RAscVS5ylG4HMBX9h7W0ZSA7CDrhXN5Lvx6g?e=V8HUmd)
[Upgrading API Versions in Azure CLI Live Test Pipeline](https://microsoft-my.sharepoint.com/:w:/p/fey/EcgPLHSkef9Mi14Rjx79N9sBvyVDO4b_V97BMcoI1HTq-A?e=Ioap3B)
[Power BI Report](https://msit.powerbi.com/groups/8de24d49-e97c-4672-9bfc-45fee0ec58f7/reports/65dfcfce-5d59-4dc9-8bc5-3726443c8fe1/ReportSection)

The below table shows modules that have regression. Code owners, please pay attention.

| Module | Pass | Fail | Pass rate | Detail | Date | Time |
| --- | --- | --- | --- | --- | --- | --- |
'''

    for entry in regression_data:
        issue_body += '| {} | {} | {} | {} | [Link]({}) | {} | {} |\n'.format(entry[0], entry[1], entry[2], entry[3], entry[4], entry[5], entry[6])

    request_body = {
        'title': 'Live test regression',
        'body': issue_body
    }
    r = requests.post('https://api.github.com/repos/Azure/azure-cli/issues',
                      headers=headers, auth=('user', GITHUB_TOKEN), json=request_body)
    print(r.status_code)
    print(r.content)


if __name__ == '__main__':
    main()
