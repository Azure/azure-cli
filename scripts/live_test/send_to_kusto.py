# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.data_format import DataFormat
from azure.kusto.ingest import (
    IngestionProperties,
    QueuedIngestClient,
)
from bs4 import BeautifulSoup
import csv
import datetime
import logging
import sys


logger = logging.getLogger(__name__)


# # authenticate with AAD application.
KUSTO_CLUSTER = sys.argv[1]
KUSTO_CLIENT_ID = sys.argv[2]
KUSTO_CLIENT_SECRET = sys.argv[3]
# get tenant id from https://docs.microsoft.com/en-us/onedrive/find-your-office-365-tenant-id
KUSTO_TENANT_ID = sys.argv[4]
KUSTO_DATABASE = sys.argv[5]
KUSTO_TABLE = sys.argv[6]
TARGET = sys.argv[7]
BUILDID = sys.argv[8]


def generate_csv_file():
    data = []
    with open(f'/mnt/vss/_work/1/{TARGET}.report.parallel.html') as file:
        bs = BeautifulSoup(file, "html.parser")
        environment = bs.find(id="environment")
        PythonVersion = environment.find(string="Python").findNext('td').text
        results = bs.find(id="results-table")
        Source = 'LiveTest'
        BuildId = BUILDID
        OSVersion = 'Ubuntu20.04'
        Module = TARGET
        Description = ''
        ExtendedProperties = ''
        for result in results.find_all('tbody'):
            Name = result.find('td', {'class': 'col-name'}).text
            Duration = result.find('td', {'class': 'col-duration'}).text
            IsSuccess = result.find('td', {'class': 'col-result'}).text
            if IsSuccess == 'Failed':
                contents = result.find('td', {'class': 'extra'}).find('div', {'class': 'log'}).contents
                Errors = ''
                for content in contents:
                    if content.name == 'br':
                        Errors += '\n'
                    if not content.name:
                        Errors += content
                    else:
                        logger.info(content.name)
            else:
                Errors = ''
            EndDateTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            StartDateTime = (datetime.datetime.now() - datetime.timedelta(seconds=int(float(Duration)))).strftime("%Y-%m-%d %H:%M:%S")
            data.append([Source, BuildId, OSVersion, PythonVersion, Module, Name, Description, StartDateTime, EndDateTime, IsSuccess, Errors, ExtendedProperties])
        
    with open(f'/mnt/vss/_work/1/{TARGET}.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)


def send_to_kusto():
    kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(KUSTO_CLUSTER, KUSTO_CLIENT_ID, KUSTO_CLIENT_SECRET, KUSTO_TENANT_ID)
    # The authentication method will be taken from the chosen KustoConnectionStringBuilder.
    client = QueuedIngestClient(kcsb)

    # there are a lot of useful properties, make sure to go over docs and check them out
    ingestion_props = IngestionProperties(

        database=KUSTO_DATABASE,
        table=KUSTO_TABLE,
        data_format=DataFormat.CSV,
    )

    # ingest from file
    result = client.ingest_from_file(f"/mnt/vss/_work/1/{TARGET}.csv", ingestion_properties=ingestion_props)
    # Inspect the result for useful information, such as source_id and blob_url
    logger.info(repr(result))


if __name__ == '__main__':
    generate_csv_file()
    send_to_kusto()
