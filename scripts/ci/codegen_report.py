#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import json
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

BUILD_ID = os.environ.get('BUILD_ID', None)
BUILD_BRANCH = os.environ.get('BUILD_BRANCH', None)


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


if __name__ == '__main__':
    generate_csv()
