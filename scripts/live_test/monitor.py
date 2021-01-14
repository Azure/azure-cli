# Monitor test results. Create issues when dropping.

import sys
import requests

DB_PWD = sys.argv[1]
GITHUB_TOKEN = sys.argv[2]


def main():
    # analyze_data()

    # Create Github issue
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    payload = {
        'title': 'Live test regression',
        # 'body': '## Test'
    }
    r = requests.post('https://api.github.com/repos/Azure/azure-cli/issues',
                      headers=headers, auth=('user', GITHUB_TOKEN), data=payload)
    print(r.content)


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
            print(new)
            print(old)

    # print(data)


if __name__ == '__main__':
    main()
