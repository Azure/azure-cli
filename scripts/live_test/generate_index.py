# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Generate index.html of testing results HTML pages.
"""
import traceback
import os
import requests
import xml.etree.ElementTree as ET


def generate(container, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE):
    """
    Generate index.html. Upload it to storage account
    :param container:
    :param container_url:
    :return:
    """
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
                print('Warning, name: {}, url: {}'.format(name, url))
            if name.endswith('.html'):
                data.append({'name': name, 'url': url})
        break
    print(data)
    html = render(data, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE)
    with open('index.html', 'w') as f:
        f.write(html)

    # Upload to storage account
    cmd = 'az storage blob upload -f index.html -c {} -n index.html --account-name clitestresultstac'.format(container)
    print('Running: ' + cmd)
    os.system(cmd)


def render(data, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE):
    content = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    table, th, td {
      border: 1px solid black;
      border-collapse: collapse;
    }
    </head>
    </style>
    <body>
    <h2>Testing results of Azure CLI</h2>
    """

    live = 'True' if USER_LIVE == '--live' else 'False'

    content += """
    <p>
    Repository: {}<br>
    Branch: {}<br>
    Commit: {}<br>
    Live: {}<br>
    </p>
    """.format(USER_REPO, USER_BRANCH, COMMIT_ID, live)

    content += """
    <p>
    <b>User Manual of Live Test Pipeline</b>
    </p>
    <p>
    <a href=https://microsoft-my.sharepoint.com/:w:/p/fey/EZGC9LwrN3RAscVS5ylG4HMBX9h7W0ZSA7CDrhXN5Lvx6g?e=V8HUmd>Word</a> 
    <a href=https://microsoft.sharepoint.com/teams/IoTToolingTeam/_layouts/OneNote.aspx?id=%2Fteams%2FIoTToolingTeam%2FShared%20Documents%2FAzure%20Management%20Experience%2FAzure%20Management%20Experience&wd=target%28AZ%20CLI%2FKnowledge%20base.one%7C18BC64EE-9328-497D-804E-6436006CA9A5%2FUser%20Manual%20of%20Live%20Test%20Pipeline%7C243EFA3E-FC7F-4612-9DA5-8E6BB2A11BD3%2F%29>OneNote</a>
    </p>
    """

    table = """
    <p><b>Test results summary</b></p>
    <table>
      <tr>
        <th>Module</th>
        <th>Passed</th>
        <th>Failed</th>
        <th>Pass rate</th>
      </tr>
    """

    for module, passed, failed, rate in testdata.modules:
        table += """
          <tr>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
          </tr>
        """.format(module, passed, failed, rate)

    table += """
      <tr>
        <td>Total</td>
        <td>{}</td>
        <td>{}</td>
        <td>{}</td>
      </tr>
    </table>
    """.format(testdata.total[1], testdata.total[2], testdata.total[3])

    content += table

    content += """
    <p><b>Reports</b></p>
    """

    for item in data:
        name = item['name']
        url = item['url']
        content += """
        <a href={}>{}</a><br>
        """.format(url, name)

    content += """
    </body>
    </html>
    """
    return content


if __name__ == '__main__':
    url = 'https://clitestresultstac.blob.core.windows.net/20200919213646live'
    try:
        generate(url)
    except:
        traceback.print_exc()
