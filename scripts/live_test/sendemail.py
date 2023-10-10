# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import sys

from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.data_format import DataFormat
from azure.kusto.ingest import (
    IngestionProperties,
    QueuedIngestClient,
    ReportLevel,
)
from bs4 import BeautifulSoup
import csv
import datetime
import generate_index
import json
import logging
import os
import re
import subprocess
import sys
import test_data
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

COMMIT_ID = sys.argv[1]
ACCOUNT_KEY = os.environ.get('ACCOUNT_KEY')
ARTIFACT_DIR = os.environ.get('ARTIFACTS_DIR')
BUILD_ID = os.environ.get('BUILD_ID')
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_KEY = os.environ.get('EMAIL_KEY')
# authenticate with AAD application.
KUSTO_CLIENT_ID = os.environ.get('KUSTO_CLIENT_ID')
KUSTO_CLIENT_SECRET = os.environ.get('KUSTO_CLIENT_SECRET')
KUSTO_CLUSTER = os.environ.get('KUSTO_CLUSTER')
KUSTO_DATABASE = os.environ.get('KUSTO_DATABASE')
KUSTO_TABLE = os.environ.get('KUSTO_TABLE')
# get tenant id from https://docs.microsoft.com/en-us/onedrive/find-your-office-365-tenant-id
KUSTO_TENANT_ID = os.environ.get('KUSTO_TENANT_ID')
PYTHON_VERSION = os.environ.get('PYTHON_VERSION')
USER_BRANCH = os.environ.get('USER_BRANCH')
USER_BRANCH_EXT = os.environ.get('USER_BRANCH_EXT')
USER_LIVE = os.environ.get('USER_LIVE')
USER_REPO = os.environ.get('USER_REPO')
USER_REPO_EXT = os.environ.get('USER_REPO_EXT')
USER_TARGET = os.environ.get('USER_TARGET')

resource_html = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>Remaining resources.html</title>
    <style>body {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 12px;
  /* do not increase min-width as some may use split screens */
  min-width: 800px;
  color: #999;
}

h1 {
  font-size: 24px;
  color: black;
}

table {
  border-collapse: collapse;
}

/******************************
 * RESULTS TABLE
 *
 * 1. Table Layout
 * 2. Sorting items
 *
 ******************************/
/*------------------
 * 1. Table Layout
 *------------------*/
#results-table {
  border: 1px solid #e6e6e6;
  color: #999;
  font-size: 12px;
  width: 100%;
}
#results-table th,
#results-table td {
  padding: 5px;
  border: 1px solid #E6E6E6;
  text-align: left;
}
#results-table th {
  font-weight: bold;
}

/*------------------
 * 2. Sorting items
 *------------------*/
.sortable {
  cursor: pointer;
}

.sort-icon {
  font-size: 0px;
  float: left;
  margin-right: 5px;
  margin-top: 5px;
  /*triangle*/
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
}
.inactive .sort-icon {
  /*finish triangle*/
  border-top: 8px solid #E6E6E6;
}
.asc.active .sort-icon {
  /*finish triangle*/
  border-bottom: 8px solid #999;
}
.desc.active .sort-icon {
  /*finish triangle*/
  border-top: 8px solid #999;
}
</style></head>
  <body onLoad="init()">
    <script>/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. */


function toArray(iter) {
    if (iter === null) {
        return null;
    }
    return Array.prototype.slice.call(iter);
}

function find(selector, elem) { // eslint-disable-line no-redeclare
    if (!elem) {
        elem = document;
    }
    return elem.querySelector(selector);
}

function findAll(selector, elem) {
    if (!elem) {
        elem = document;
    }
    return toArray(elem.querySelectorAll(selector));
}

function sortColumn(elem) {
    toggleSortStates(elem);
    const colIndex = toArray(elem.parentNode.childNodes).indexOf(elem);
    let key;
    key = keyAlpha;
    sortTable(elem, key(colIndex));
}

function showFilters() {
    let visibleString = getQueryParameter('visible') || 'all';
    visibleString = visibleString.toLowerCase();
    const checkedItems = visibleString.split(',');

    const filterItems = document.getElementsByClassName('filter');
    for (let i = 0; i < filterItems.length; i++) {
        filterItems[i].hidden = false;

        if (visibleString != 'all') {
            filterItems[i].checked = checkedItems.includes(filterItems[i].getAttribute('data-test-result'));
        }
    }
}

function getQueryParameter(name) {
    const match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
    return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
}

function init () { // eslint-disable-line no-unused-vars
    resetSortHeaders();

    showFilters();

    sortColumn(find('.initial-sort'));

    findAll('.sortable').forEach(function(elem) {
        elem.addEventListener('click',
            function() {
                sortColumn(elem);
            }, false);
    });
}

function sortTable(clicked, keyFunc) {
    const rows = findAll('.results-table-row');
    const reversed = !clicked.classList.contains('asc');
    const sortedRows = sort(rows, keyFunc, reversed);
    /* Whole table is removed here because browsers acts much slower
     * when appending existing elements.
     */
    const thead = document.getElementById('results-table-head');
    document.getElementById('results-table').remove();
    const parent = document.createElement('table');
    parent.id = 'results-table';
    parent.appendChild(thead);
    sortedRows.forEach(function(elem) {
        parent.appendChild(elem);
    });
    document.getElementsByTagName('BODY')[0].appendChild(parent);
}

function sort(items, keyFunc, reversed) {
    const sortArray = items.map(function(item, i) {
        return [keyFunc(item), i];
    });

    sortArray.sort(function(a, b) {
        const keyA = a[0];
        const keyB = b[0];

        if (keyA == keyB) return 0;

        if (reversed) {
            return keyA < keyB ? 1 : -1;
        } else {
            return keyA > keyB ? 1 : -1;
        }
    });

    return sortArray.map(function(item) {
        const index = item[1];
        return items[index];
    });
}

function keyAlpha(colIndex) {
    return function(elem) {
        return elem.childNodes[1].childNodes[colIndex].firstChild.data.toLowerCase();
    };
}

function resetSortHeaders() {
    findAll('.sort-icon').forEach(function(elem) {
        elem.parentNode.removeChild(elem);
    });
    findAll('.sortable').forEach(function(elem) {
        const icon = document.createElement('div');
        icon.className = 'sort-icon';
        icon.textContent = 'vvv';
        elem.insertBefore(icon, elem.firstChild);
        elem.classList.remove('desc', 'active');
        elem.classList.add('asc', 'inactive');
    });
}

function toggleSortStates(elem) {
    //if active, toggle between asc and desc
    if (elem.classList.contains('active')) {
        elem.classList.toggle('asc');
        elem.classList.toggle('desc');
    }

    //if inactive, reset all other functions and add ascending active
    if (elem.classList.contains('inactive')) {
        resetSortHeaders();
        elem.classList.remove('inactive');
        elem.classList.add('active');
    }
}

</script>
    <h1>Resources to clean up</h1>
    <table id="results-table">
      <thead id="results-table-head">
        <tr>
          <th class="sortable initial-sort" col="module">Module</th>
          <th class="sortable" col="test-case">Test Case</th>
          <th class="sortable" col="date">Date</th>
          <th class="sortable" col="resource-group">Resource Group</th>
        </tr>
    </table>
  </body>
</html>
"""


def main():
    logger.info('Enter main()')

    logger.info(BUILD_ID)
    logger.info(USER_REPO)
    logger.info(USER_BRANCH)
    logger.info(USER_TARGET)
    logger.info(USER_LIVE)
    logger.info(ARTIFACT_DIR)
    logger.info(EMAIL_ADDRESS)
    logger.info(COMMIT_ID)

    # Collect statistics
    testdata = test_data.TestData(ARTIFACT_DIR)
    testdata.collect()

    # Summary data and send to kusto db
    summary_data(testdata)

    # Upload results to storage account, container
    container = ''
    try:
        logger.info('Uploading test results to storage account...')
        container = get_container_name()
        upload_files(container)
    except Exception:
        logger.exception(traceback.format_exc())

    # Generate index.html, send email
    try:
        # Generate index.html
        container_url = 'https://clitestresultstac.blob.core.windows.net/' + container
        html_content = generate_index.generate(container, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE, USER_TARGET, ACCOUNT_KEY, USER_REPO_EXT, USER_BRANCH_EXT)
        # Send email
        send_email(html_content)
    except Exception:
        logger.exception(traceback.format_exc())

    get_remaining_tests()
    logger.info('Exit main()')


def get_remaining_tests():
    # get residual resources after live test finished
    logger.info('Enter get_remaining_tests()')
    cmd = ['az', 'group', 'list', '--tag', 'module', '--query', '[][name, tags]']
    logger.info(cmd)
    out = subprocess.run(cmd, capture_output=True)
    remaing_tests = json.loads(out.stdout) if out.stdout else []
    if remaing_tests:
        # sorted remaing tests by module name and test name
        sorted_tests = sorted(remaing_tests, key=lambda x: (x[1]['module'], x[1]['test']))
        soup = BeautifulSoup(resource_html, 'html.parser')
        for test in sorted_tests:
            module = test[1]['module']
            test_name = test[1]['test']
            date = test[1]['date']
            group = test[0]
            tbody = soup.new_tag('tbody', **{'class': 'results-table-row'})
            tr = soup.new_tag('tr')
            td_module = soup.new_tag('td', **{'class': 'col-module'})
            td_module.string = module
            tr.append(td_module)
            td_test = soup.new_tag('td', **{'class': 'col-test-case'})
            td_test.string = test_name
            tr.append(td_test)
            td_date = soup.new_tag('td', **{'class': 'col-date'})
            td_date.string = date
            tr.append(td_date)
            td_group = soup.new_tag('td', **{'class': 'col-resource-group'})
            td_group.string = group
            tr.append(td_group)
            tbody.append(tr)
            soup.table.append(tbody)
        with open('resource.html', 'w') as f:
            f.write(str(soup))
            logger.info('resource.html: ' + str(soup))
        cmd = 'az storage blob upload -f resource.html -c {} -n resource.html --account-name clitestresultstac --account-key {}'.format(BUILD_ID, ACCOUNT_KEY)
        logger.info('Running: ' + cmd)
        os.system(cmd)


def summary_data(testdata):
    # summary data by module and platform
    logger.info('Enter summary_data_by_module()')
    modules = [module[0].split('.')[0] for module in testdata.modules]
    data = []
    for idx, module in enumerate(modules):
        total_test = testdata.modules[idx][1] + testdata.modules[idx][2]
        passed = testdata.modules[idx][1]
        failed = testdata.modules[idx][2]
        html_name = '.'.join([module, 'report.html'])
        src_soup = ''
        for root, dirs, files in os.walk(ARTIFACT_DIR):
            First = True
            dst_html = os.path.join(root, html_name)
            for file in files:
                if file.startswith(module) and file.endswith('html') and First:
                    First = False
                    platform = file.split('.')[1]
                    first = os.path.join(root, file)
                    try:
                        data.extend(html_to_csv(first, module, platform))
                    except Exception as e:
                        logger.error(f'Error load {first}')
                        First = True
                        continue
                    with open(first, 'r') as f:
                        src_html = f.read()
                        src_soup = BeautifulSoup(src_html, 'html.parser')
                        th = src_soup.find('thead', id='results-table-head')
                        tr = th.find('tr')
                        new_th = src_soup.new_tag('th', **{'class': 'sortable', 'col': 'platform'})
                        new_th.string = 'Platform'
                        tr.insert(2, new_th)
                        tbodys = src_soup.findAll('tbody')
                        for tbody in tbodys:
                            tr = tbody.find('tr')
                            new_col = src_soup.new_tag('td', **{'class': 'col-platform'})
                            new_col.string = platform
                            tr.insert(2, new_col)
                        src_soup.find('title').string = f'{module}.html'
                        src_soup.find('h1').string = f'{module}.html'
                        env = src_soup.find('table', id='environment')
                        if env:
                            env_trs = env.findAll('tr')
                            for tr in env_trs:
                                if 'Platform' in tr.text:
                                    tr.decompose()
                        inputs = src_soup.findAll('input')
                        for i in inputs:
                            if 'disabled' in i.attrs:
                                del i['disabled']
                        src_soup.find('span', {'class': 'passed'}).string = f'{passed} passed'
                        src_soup.find('span', {'class': 'failed'}).string = f'{failed} failed'
                        # src_soup.find('span', {'class': 'skipped'}).string = f'{skiped} skipped'

                elif file.startswith(module) and file.endswith('html'):
                    platform = file.split('.')[1]
                    other = os.path.join(root, file)
                    try:
                        data.extend(html_to_csv(other, module, platform))
                    except Exception as e:
                        logger.error(f'Error load {other}')
                        continue
                    with open(other, 'r') as f:
                        other_html = f.read()
                        other_soup = BeautifulSoup(other_html, 'html.parser')
                        tbodys = other_soup.findAll('tbody')
                        for tbody in tbodys:
                            tr = tbody.find('tr')
                            new_col = src_soup.new_tag('td', **{'class': 'col-platform'})
                            new_col.string = platform
                            tr.insert(2, new_col)
                    table = src_soup.find('table', id='results-table')
                    for tbody in tbodys:
                        table.append(tbody)
                    p1 = src_soup.find('p', string=re.compile('.*tests ran in.*'))
                    duration = p1.string.split(' ')[-3]
                    p2 = other_soup.find('p', string=re.compile('.*tests ran in.*'))
                    duration2 = p2.string.split(' ')[-3]
                    duration = float(duration) + float(duration2)
                    p1.string = f'{total_test} tests ran in {duration} seconds. '

        with open(dst_html, 'w') as f:
            f.write(str(src_soup))

    # send to kusto db
    if USER_TARGET.lower() in ['all', ''] \
            and USER_REPO == 'https://github.com/Azure/azure-cli.git' \
            and USER_REPO_EXT == 'https://github.com/Azure/azure-cli-extensions.git' \
            and USER_BRANCH == 'dev' and USER_BRANCH_EXT == 'main' \
            and USER_LIVE == '--live' and data:
        send_to_kusto(data)

    for root, dirs, files in os.walk(ARTIFACT_DIR):
        for file in files:
            if len(file.split('.')) > 3 and file.endswith('html'):
                os.remove(os.path.join(root, file))


def html_to_csv(html_file, module, platform):
    data = []
    if os.path.exists(html_file):
        with open(html_file) as file:
            bs = BeautifulSoup(file, "html.parser")
            results = bs.find(id="results-table")
            Source = 'LiveTest'
            BuildId = BUILD_ID
            Module = module
            Description = ''
            ExtendedProperties = ''
            for result in results.find_all('tbody'):
                Name = result.find('td', {'class': 'col-name'}).text.split('::')[-1]
                Duration = result.find('td', {'class': 'col-duration'}).text
                Status = result.find('td', {'class': 'col-result'}).text
                if Status == 'Failed':
                    contents = result.find('td', {'class': 'extra'}).find('div', {'class': 'log'}).contents
                    Details = ''
                    for content in contents:
                        if content.name == 'br':
                            Details += '\n'
                        elif not content.name:
                            Details += content
                        else:
                            logger.info(content.name) if content.name != 'span' else None
                else:
                    Details = ''
                EndDateTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                StartDateTime = (datetime.datetime.now() - datetime.timedelta(seconds=int(float(Duration)))).strftime(
                    "%Y-%m-%d %H:%M:%S")
                data.append(
                    [Source, BuildId, platform, PYTHON_VERSION, Module, Name, Description, StartDateTime, EndDateTime,
                     Duration, Status, Details, ExtendedProperties])
    return data


def send_to_kusto(data):
    logger.info('Start send csv data to kusto db')

    with open(f'{ARTIFACT_DIR}/livetest.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)
    logger.info('Finish generate csv file for live test.')

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
    result = client.ingest_from_file(f"{ARTIFACT_DIR}/livetest.csv", ingestion_properties=ingestion_props)
    # Inspect the result for useful information, such as source_id and blob_url
    print(repr(result))
    logger.info('Finsh send live test csv data to kusto db.')


def get_container_name():
    """
    Generate container name in storage account. It is also an identifier of the pipeline run.
    :return:
    """
    logger.info('Enter get_container_name()')
    name = BUILD_ID
    logger.info('Exit get_container_name()')
    return name


def upload_files(container):
    """
    Upload html and json files to container
    :param container:
    :return:
    """
    logger.info('Enter upload_files()')

    # Create container
    cmd = 'az storage container create -n {} --account-name clitestresultstac --account-key {} --public-access container'.format(container, ACCOUNT_KEY)
    os.system(cmd)

    # Upload files
    for root, dirs, files in os.walk(ARTIFACT_DIR):
        for name in files:
            if name.endswith('html') or name.endswith('json'):
                fullpath = os.path.join(root, name)
                cmd = 'az storage blob upload -f {} -c {} -n {} --account-name clitestresultstac --account-key {}'.format(fullpath, container, name, ACCOUNT_KEY)
                os.system(cmd)

    logger.info('Exit upload_files()')


def send_email(html_content):
    logger.info('Sending email...')
    from azure.communication.email import EmailClient

    client = EmailClient.from_connection_string(EMAIL_KEY);
    content = {
        "subject": "Test results of Azure CLI",
        "html": html_content,
    }

    recipients = ''

    if EMAIL_ADDRESS != '':
        recipients = {
            "to": [
                {
                    "address": EMAIL_ADDRESS
                },
            ]
        }
    elif USER_TARGET.lower() in ['all', ''] \
            and USER_REPO == 'https://github.com/Azure/azure-cli.git' \
            and USER_REPO_EXT == 'https://github.com/Azure/azure-cli-extensions.git' \
            and USER_BRANCH == 'dev' and USER_BRANCH_EXT == 'main' \
            and USER_LIVE == '--live' and EMAIL_ADDRESS == '':
        recipients = {
            "to": [
                {
                    "address": "AzPyCLI@microsoft.com"
                },
                {
                    "address": "antcliTest@microsoft.com"
                }
            ]
        }

    if recipients:
        message = {
            "content": content,
            "senderAddress": "DoNotReply@561634e2-1674-4377-9975-10a9197437d7.azurecomm.net",
            "recipients": recipients
        }

        client.begin_send(message)
        logger.info('Finish sending email')
    else:
        logger.info('No recipients, skip sending email')


if __name__ == '__main__':
    main()
