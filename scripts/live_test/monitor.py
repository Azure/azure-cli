#


def main():
    import mysql.connector
    # Connect
    cnx = mysql.connector.connect(user='fey@clisqldbserver',
                                  password=DB_PWD,
                                  host='clisqldbserver.mysql.database.azure.com',
                                  database='clidb')
    sql = ''


if '__name__' == '__main__':
    main()
