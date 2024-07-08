#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.data_format import DataFormat
from azure.kusto.ingest import (
    IngestionProperties,
    QueuedIngestClient,
    ReportLevel,
)
import csv
import datetime
import json
import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

BUILD_ID = os.environ.get('BUILD_ID', None)
BUILD_BRANCH = os.environ.get('BUILD_BRANCH', None)
# authenticate with AAD application.
KUSTO_CLIENT_ID = os.environ.get('KUSTO_CLIENT_ID')
KUSTO_CLIENT_SECRET = os.environ.get('KUSTO_CLIENT_SECRET')
KUSTO_CLUSTER = os.environ.get('KUSTO_CLUSTER')
KUSTO_DATABASE = os.environ.get('KUSTO_DATABASE')
KUSTO_TABLE = os.environ.get('KUSTO_TABLE')
# get tenant id from https://docs.microsoft.com/en-us/onedrive/find-your-office-365-tenant-id
KUSTO_TENANT_ID = os.environ.get('KUSTO_TENANT_ID')


def generate_csv():
    data = []
    with open(f'/tmp/codegen_report.json', 'r') as file:
        ref = json.load(file)
    codegenv1 = ref['codegenV1']
    codegenv2 = ref['codegenV2']
    total = ref['total']
    manual = total - codegenv1 - codegenv2
    is_release = True if BUILD_BRANCH == 'release' else False
    date = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
    data.append([BUILD_ID, manual, codegenv1, codegenv2, total, is_release, date])
    logger.info(f'Finish generate data for codegen report: {data}')
    return data


def send_to_kusto(data):
    logger.info('Start send codegen report csv data to kusto db')

    with open(f'/tmp/codegen_report.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

    kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(KUSTO_CLUSTER, KUSTO_CLIENT_ID, KUSTO_CLIENT_SECRET, KUSTO_TENANT_ID)
    # The authentication method will be taken from the chosen KustoConnectionStringBuilder.
    client = QueuedIngestClient(kcsb)

    # there are a lot of useful properties, make sure to go over docs and check them out
    ingestion_props = IngestionProperties(
        database=KUSTO_DATABASE,
        table=KUSTO_TABLE,
        data_format=DataFormat.CSV,
        report_level=ReportLevel.FailuresAndSuccesses
    )

    # ingest from file
    result = client.ingest_from_file(f"/tmp/codegen_report.csv", ingestion_properties=ingestion_props)
    # Inspect the result for useful information, such as source_id and blob_url
    print(repr(result))
    logger.info('Finsh send codegen report csv data to kusto db.')


if __name__ == '__main__':
    send_to_kusto(generate_csv())
