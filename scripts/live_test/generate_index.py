# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Generate index.html of testing results HTML pages.
"""
import traceback
import os
import re
import requests
import xml.etree.ElementTree as ET
import logging


logger = logging.getLogger(__name__)


def generate(container, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE, USER_TARGET):
    """
    Generate index.html. Upload it to storage account
    :param container:
    :param container_url:
    :return: a HTML string
    """
    logger.warning('Enter generate()')
    # [{'name': name, 'url': url}]
    data = []
    url = container_url + '?restype=container&comp=list'
    content = requests.get(url).content
    logger.warning(content)
    root = ET.fromstring(content)
    for blobs in root:
        for blob in blobs:
            name = url = ''
            for e in blob:
                if e.tag == 'Name':
                    name = e.text
                if e.tag == 'Url':
                    url = e.text
            if name == '' or url == '':
                logger.warning('[Warning] Blob\'s name or url is empty, name: {}, url: {}'.format(name, url))
            if name.endswith('.html'):
                data.append({'name': name, 'url': url})
        break
    logger.warning(data)
    html = render(data, container, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE)
    with open('index.html', 'w') as f:
        f.write(html)

    # Upload to storage account
    cmd = 'az storage blob upload -f index.html -c {} -n index.html --account-name clitestresultstac --overwrite'.format(container)
    logger.warning('Running: ' + cmd)
    os.system(cmd)

    # Upload to latest container if it is a full live test of official repo dev branch
    if USER_REPO == 'https://github.com/Azure/azure-cli.git' and USER_BRANCH == 'dev' and USER_TARGET == '' and USER_LIVE == '--live':
        cmd = 'az storage blob upload -f index.html -c latest -n index.html --account-name clitestresultstac --overwrite'
        logger.warning('Running: ' + cmd)
        os.system(cmd)

    logger.warning('Exit generate()')
    return html


def render(data, container, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE):
    """
    Return a HTML string
    :param data:
    :param container:
    :param container_url:
    :param testdata:
    :param USER_REPO:
    :param USER_BRANCH:
    :param COMMIT_ID:
    :param USER_LIVE:
    :return:
    """
    logger.warning('Enter render()')
    content = """
    <!DOCTYPE html>
    <html>
    <head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">
    <style>
    table, th, td {
      border: 1px solid black;
      border-collapse: collapse;
    }
    </style>
    </head>
    <body>
    <h2>Testing results of Azure CLI</h2>
    """

    live = 'True' if USER_LIVE == '--live' else 'False'
    date = container.split('-')[0]

    content += """
    <p>
    Repository: {}<br>
    Branch: {}<br>
    Commit: {}<br>
    Live: {}<br>
    Date: {}
    </p>
    """.format(USER_REPO, USER_BRANCH, COMMIT_ID, live, date)

    content += """
    <p>
    <b>Pass: {}, Fail: {}, Pass rate: {}</b>
    </p>
    """.format(testdata.total[1], testdata.total[2], testdata.total[3])

    content += """
    <p>
    <a href=https://microsoft-my.sharepoint.com/:w:/p/fey/EZGC9LwrN3RAscVS5ylG4HMBX9h7W0ZSA7CDrhXN5Lvx6g?e=V8HUmd>User Manual of Live Test Pipeline</a>
    (Please read it)
    <br>
    <a href=https://microsoft-my.sharepoint.com/:w:/p/fey/EcgPLHSkef9Mi14Rjx79N9sBvyVDO4b_V97BMcoI1HTq-A?e=Ioap3B>Upgrading API Versions in Azure CLI Live Test Pipeline</a>
    (Advanced feature)
    <br>
    <a href=https://msit.powerbi.com/groups/8de24d49-e97c-4672-9bfc-45fee0ec58f7/reports/65dfcfce-5d59-4dc9-8bc5-3726443c8fe1/ReportSection>Power BI Report</a>
    (History data, beautiful charts and tables)
    </p>
    """

    table = """
    <p><b>Test results summary</b></p>
    <table>
      <tr>
        <th>Module</th>
        <th>Pass</th>
        <th>Fail</th>
        <th>Pass rate</th>
        <th>Reports</th>
      </tr>
    """

    table += """
      <tr>
        <td>Total</td>
        <td>{}</td>
        <td>{}</td>
        <td>{}</td>
        <td>N/A</td>
      </tr>
    """.format(testdata.total[1], testdata.total[2], testdata.total[3])

    for module, passed, failed, rate in testdata.modules:
        reports = ''
        for x in data:
            name = x['name']
            url = x['url']
            if name.startswith(module + '.'):
                display_name = 'report'
                if 'parallel' in name:
                    display_name = 'parallel'
                elif 'sequential' in name:
                    display_name = 'sequential'
                try:
                    html = requests.get(url).content.__str__()
                    pattern = re.compile('\\d+ tests ran in')
                    match = pattern.search(html)
                    number = match.group().split()[0]
                    if number.isdigit():
                        display_name += '(' + number + ')'
                except:
                    logger.exception(traceback.print_exc())
                reports += '<a href="{}">{}</a> '.format(url, display_name)
        table += """
          <tr>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
          </tr>
        """.format(module, passed, failed, rate, reports)

    table += """
    </table>
    """
    content += table

    # content += """
    # <p><b>Reports</b></p>
    # """
    #
    # for item in data:
    #     name = item['name']
    #     url = item['url']
    #     content += """
    #     <a href={}>{}</a><br>
    #     """.format(url, name)

    content += """
    </body>
    </html>
    """

    logger.warning(content)
    logger.warning('Exit render()')
    return content


def main():
    url = 'https://clitestresultstac.blob.core.windows.net/20200919213646live'
    try:
        generate(url)
    except:
        logger.exception(traceback.print_exc())


if __name__ == '__main__':
    main()
