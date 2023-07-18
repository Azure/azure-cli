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
from collections import OrderedDict
import bisect
import argparse

TEMPLATE_FILE_NAME='formula_template.txt'
CLI_VERSION=os.environ['CLI_VERSION']
HOMEBREW_UPSTREAM_URL=os.environ['HOMEBREW_UPSTREAM_URL']
HOMEBREW_FORMULAR_LATEST="https://raw.githubusercontent.com/Homebrew/homebrew-core/master/Formula/azure-cli.rb"


def main():
    print('Generate formula for Azure CLI homebrew release.')

    parser = argparse.ArgumentParser(prog='formula_generator.py')
    parser.set_defaults(func=generate_formula)
    parser.add_argument('-b', dest='build_method', choices=['update_existing', 'use_template'], help='The build method, default is update_existing, the other option is use_template.')
    args = parser.parse_args()
    args.func(**vars(args))

def generate_formula(build_method: str, **_):
    content = ''
    if build_method is None or build_method == 'update_existing':
        content = update_formula()
    elif build_method == 'use_template':
        content = generate_formula_with_template()
    with open('azure-cli.rb', mode='w') as fq:
        fq.write(content)


def generate_formula_with_template() -> str:
    """Generate a brew formula by using a template"""
    template_path = os.path.join(os.path.dirname(__file__), TEMPLATE_FILE_NAME)
    with open(template_path, mode='r') as fq:
        template_content = fq.read()

    template = jinja2.Template(template_content)
    content = template.render(
        cli_version=CLI_VERSION,
        upstream_url=HOMEBREW_UPSTREAM_URL,
        upstream_sha=compute_sha256(HOMEBREW_UPSTREAM_URL),
        resources=collect_resources(),
        bottle_hash=last_bottle_hash()
    )
    if not content.endswith('\n'):
        content += '\n'
    return content


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


def collect_resources_dict() -> dict:
    nodes = make_graph('azure-cli')
    filtered_nodes = {nodes[node_name]['name']: nodes[node_name] for node_name in sorted(nodes) if resource_filter(node_name)}
    return filtered_nodes


def resource_filter(name: str) -> bool:
    # TODO remove need for any filters and delete this method.
    return not name.startswith('azure-cli') and name not in ('futures', 'jeepney', 'entrypoints')


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


def update_formula() -> str:
    """Generate a brew formula by updating the existing one"""
    nodes = collect_resources_dict()

    resp = requests.get(HOMEBREW_FORMULAR_LATEST)
    resp.raise_for_status()
    text = resp.text

    # update url and sha256 of azure-cli
    text = re.sub('url ".*"', 'url "{}"'.format(HOMEBREW_UPSTREAM_URL), text, 1)
    upstream_sha = compute_sha256(HOMEBREW_UPSTREAM_URL)
    text = re.sub('sha256 ".*"', 'sha256 "{}"'.format(upstream_sha), text, 1)
    text = re.sub('.*revision.*\n', '', text, 1)  # remove revision for previous version if exists
    pack = None
    packs_to_remove = set()
    lines = text.split('\n')
    node_index_dict = OrderedDict()
    line_idx_to_remove = set()
    upgrade = False
    for idx, line in enumerate(lines):
        # In released formula, the url is in the release tag format, such as
        # "https://github.com/Azure/azure-cli/archive/azure-cli-2.17.1.tar.gz".
        # version is extracted from url. During build, the url is in the format like
        # "https://codeload.github.com/Azure/azure-cli/legacy.tar.gz/7e09fd50c9ef02e1ed7d4709c7ab1a71acd3840b".
        # We need to add the version explicitly after url.
        # We will change the url in our release pipeline and remove version.
        if line.startswith("  url"):
            lines[idx] = lines[idx] + '\n' + '  version "{}"'.format(CLI_VERSION)
        elif line.strip().startswith("resource"):
            m = re.search(r'resource "(.*)" do', line)
            if m is not None:
                pack = m.group(1)
                node_index_dict[pack] = idx
        elif pack is not None:
            if line.startswith("    url"):
                #update the url of package
                if pack in nodes.keys():
                    url_match = re.search(r'url "(.*)"', line)
                    if url_match is not None and nodes[pack]['url'] != url_match.group(1):
                        lines[idx] = re.sub('url ".*"', 'url "{}"'.format(nodes[pack]['url']), line, 1)
                        upgrade = True
                else:
                    packs_to_remove.add(pack)
            elif line.startswith("    sha256"):
                #update the sha256 of package
                if pack in nodes.keys():
                    lines[idx] = re.sub('sha256 ".*"', 'sha256 "{}"'.format(nodes[pack]['checksum']), line, 1)
                    del nodes[pack]
            elif line.startswith("  end"):
                pack = None
                upgrade = False
            elif upgrade:  # In case of upgrading, remove any patch following url and sha256 but before end
                line_idx_to_remove.add(idx)
        elif line.strip().startswith('def install'):
            if nodes:
                # add new dependency packages
                for node_name, node in nodes.items():
                    # find the right place to insert the new resource per alphabetic order
                    i = bisect.bisect_left(list(node_index_dict.keys()), node_name)
                    line_idx = list(node_index_dict.items())[i][1]
                    resource = RESOURCE_TEMPLATE.render(resource=node)
                    lines[line_idx] = resource + '\n\n' + lines[line_idx]
    lines = [line for idx, line in enumerate(lines) if idx not in line_idx_to_remove]
    new_text = "\n".join(lines)

    # remove dependency packages that are no longer needed
    for pack in packs_to_remove:
        new_text = re.sub(r'resource "{}" do.*?\n  end\n\s+'.format(pack), '', new_text, flags=re.DOTALL)
    return new_text


if __name__ == '__main__':
    main()
