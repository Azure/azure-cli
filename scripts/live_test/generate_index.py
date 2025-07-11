# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Generate index.html of testing results HTML pages.
"""
import datetime
import traceback
import os
import re
import requests
import xml.etree.ElementTree as ET
import logging
STATIC_WEB_URL = os.environ.get('STATIC_WEB_URL')

logger = logging.getLogger(__name__)


def generate(ACCOUNT_NAME, container, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE, USER_REPO_EXT, USER_BRANCH_EXT):
    """
    Generate index.html. Upload it to storage account
    :param container:
    :return: a HTML string
    """
    logger.warning('Enter generate()')
    html = render(testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE, USER_REPO_EXT, USER_BRANCH_EXT)
    with open('index.html', 'w') as f:
        f.write(html)

    # Upload to storage account
    cmd = f'az storage blob upload -f index.html -c {container} -n index.html --account-name {ACCOUNT_NAME} --auth-mode login --overwrite'
    logger.warning('Running: ' + cmd)
    os.system(cmd)

    # Upload to $web container
    cmd = f"az storage blob upload -f index.html -c '$web' -n index.html --account-name {ACCOUNT_NAME} --auth-mode login --overwrite"
    logger.warning('Running: ' + cmd)
    os.system(cmd)

    logger.warning('Exit generate()')
    return html


def sort_by_module_name(item):
    # Sort test data by module name,
    # and modules starting with `ext-` need to be placed after modules not starting with `ext-`,
    if item[0].startswith("ext-"):
        return 1, item[0][4:]  # sort with higher priority
    else:
        return 0, item[0]  # sort with lower priority


def render(testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE, USER_REPO_EXT, USER_BRANCH_EXT):
    """
    Return a HTML string
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
    date = datetime.date.today()

    content += """
    <p>
    Repository: {}<br>
    Branch: {}<br>
    Repository of extension: {}<br>
    Branch of extension: {}<br>
    Commit: {}<br>
    Live: {}<br>
    Date: {}
    </p>
    """.format(USER_REPO, USER_BRANCH, USER_REPO_EXT, USER_BRANCH_EXT, COMMIT_ID, live, date)

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
      </tr>
    """

    table += """
      <tr>
        <td>Total</td>
        <td>{}</td>
        <td>{}</td>
        <td>{}</td>
      </tr>
    """.format(testdata.total[1], testdata.total[2], testdata.total[3])

    sorted_modules = sorted(testdata.modules, key=sort_by_module_name)

    for module, passed, failed, rate in sorted_modules:
        table += """
          <tr>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
          </tr>
        """.format('<a href="{}">{}</a> '.format(STATIC_WEB_URL+module+'.report.html', module),
                   passed, failed, rate)

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
