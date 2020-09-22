# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Generate index.html of testing results HTML pages.
"""
import traceback
import requests
import xml.etree.ElementTree as ET


def generate(container_url):
    data = []
    url = container_url + '?restype=container&comp=list'
    try:
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
                    print('Warning, name: {}, ')
                if name.endswith('.html'):
                    data.append({'name': name, 'url': url})
            break
        print(data)
        html = render(data, container_url)
        with open('index.html', 'w') as f:
            f.write(html)
    except:
        traceback.print_exc()


def render(data, container_url):
    content = """
    <!DOCTYPE html>
    <html>
    <head>
    </head>
    <body>
    <h2>Testing results in {}</h2>
    """.format(container_url)
    for item in data:
        name = item['name']
        url = item['url']
        content += """
        <p><a href={}>{}</a></p>
        """.format(url, name)
    content += """
    </body>
    </html>
    """
    return content


if __name__ == '__main__':
    url = 'https://clitestresultstac.blob.core.windows.net/20200919213646live'
    generate(url)
