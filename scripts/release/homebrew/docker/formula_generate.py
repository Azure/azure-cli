# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import re
from typing import List, Tuple

import requests
import jinja2
from poet.poet import make_graph, RESOURCE_TEMPLATE

TEMPLATE_FILE_NAME='formula_template.txt'
HOMEBREW_UPSTREAM_URL=os.environ['HOMEBREW_UPSTREAM_URL']
HOMEBREW_FORMULAR_LATEST="https://raw.githubusercontent.com/Homebrew/homebrew-core/master/Formula/azure-cli.rb"


def main():
    print('Generate formular for Azure CLI homebrew release.')

    template_path = os.path.join(os.path.dirname(__file__), TEMPLATE_FILE_NAME)
    with open(template_path, mode='r') as fq:
        template_content = fq.read()

    template = jinja2.Template(template_content)
    content = template.render(
        upstream_url=HOMEBREW_UPSTREAM_URL,
        upstream_sha=compute_sha256(HOMEBREW_UPSTREAM_URL),
        resources=collect_resources(),
        bottle_hash=last_bottle_hash()
    )
    if not content.endswith('\n'):
        content += '\n'

    with open('azure-cli.rb', mode='w') as fq:
        fq.write(content)

def compute_sha256(resource_url: str) -> str:
    import hashlib
    sha256 = hashlib.sha256()
    resp = requests.get(resource_url)
    resp.raise_for_status()
    sha256.update(resp.content)
    
    return sha256.hexdigest()


def collect_resources() -> str:
    nodes = make_graph('azure-cli')
    nodes_render = []
    for node_name in sorted(nodes):
        if not resource_filter(node_name):
            continue

        nodes_render.append(RESOURCE_TEMPLATE.render(resource=nodes[node_name]))
    return '\n\n'.join(nodes_render)


def resource_filter(name: str) -> bool:
    return not name.startswith('azure-cli') and name not in ('futures')


def last_bottle_hash():
    """Fetch the bottle do ... end from the latest brew formula"""
    resp = requests.get(HOMEBREW_FORMULAR_LATEST)
    resp.raise_for_status()

    lines = resp.text.split('\n')
    look_for_end = False
    start = 0
    end = 0
    for idx, content in enumerate(lines):
        if look_for_end:
            if 'end' in content:
                end = idx
                break
        else:
            if 'bottle do' in content:
                start = idx
                look_for_end = True
    
    return '\n'.join(lines[start: end + 1])


if __name__ == '__main__':
    main()
