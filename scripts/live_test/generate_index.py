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


def generate(container, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE, USER_TARGET):
    """
    Generate index.html. Upload it to storage account
    :param container:
    :param container_url:
    :return:
    """
    print('Enter generate()')
    # [{'name': name, 'url': url}]
    data = []
    url = container_url + '?restype=container&comp=list'
    content = requests.get(url).content
    # print(content)
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
                print('[Warning] Blob\'s name or url is empty, name: {}, url: {}'.format(name, url))
            if name.endswith('.html'):
                data.append({'name': name, 'url': url})
        break
    print(data)
    html = render(data, container, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE)
    with open('index.html', 'w') as f:
        f.write(html)

    # Upload to storage account
    cmd = 'az storage blob upload -f index.html -c {} -n index.html --account-name clitestresultstac'.format(container)
    print('Running: ' + cmd)
    os.system(cmd)

    # Upload to latest container if it is a full live test of official repo dev branch
    if USER_REPO == 'https://github.com/Azure/azure-cli.git' and USER_BRANCH == 'dev' and USER_TARGET == '' and USER_LIVE == '--live':
        cmd = 'az storage blob upload -f index.html -c latest -n index.html --account-name clitestresultstac'
        print('Running: ' + cmd)
        os.system(cmd)

    print('Exit generate()')


def render(data, container, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE):
    print('Enter render()')
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
        <td></td>
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
                    traceback.print_exc()
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

    print(content)
    print('Exit render()')
    return content


if __name__ == '__main__':
    url = 'https://clitestresultstac.blob.core.windows.net/20200919213646live'
    try:
        generate(url)
    except:
        traceback.print_exc()
