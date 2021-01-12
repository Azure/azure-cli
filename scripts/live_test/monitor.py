# Monitor test results. Create issues when dropping.

import sys

DB_PWD = sys.argv[1]


def main():
    import mysql.connector
    # Connect
    cnx = mysql.connector.connect(user='fey@clisqldbserver',
                                  password=DB_PWD,
                                  host='clisqldbserver.mysql.database.azure.com',
                                  database='clidb')
    cursor = cnx.cursor()
    sql = 'select module from t2 group by module'
    cursor.execute(sql)
    modules = []
    for value in cursor:
        if not value[0].startswith('ext-'):
            modules.append(value[0])

    print(modules)

    for module in modules:
        sql = 'select t2.module from t1 join t2 on t1.id = t2.id'
        cursor.execute(sql)


if __name__ == '__main__':
    main()
