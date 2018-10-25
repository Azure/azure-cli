#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import sys
import tempfile
import hashlib
import shutil
from collections import OrderedDict
from sh import pip, git

try:
    # Attempt to load python 3 module
    from urllib.request import urlopen
except ImportError:
    # Import python 2 version
    from urllib2 import urlopen

HOMEBREW_REPO_URL = 'https://github.com/Homebrew/homebrew-core'
AZURE_CLI_FORMULA_PATH = os.path.join('Formula', 'azure-cli.rb')

CLI_VERSION = os.environ['CLI_VERSION']
UPSTREAM_URL = os.environ['UPSTREAM_URL']
BUILD_ARTIFACTS_DIR = os.environ.get('BUILD_ARTIFACT_DIR')

def get_homebrew_formula():
    tmp_dir = tempfile.mkdtemp()
    git(['clone', '--depth', '1', HOMEBREW_REPO_URL, tmp_dir], _out=sys.stdout, _err=sys.stdout)
    formula_path = os.path.join(tmp_dir, AZURE_CLI_FORMULA_PATH)
    formula_content = []
    with open(formula_path) as f:
        formula_content = f.readlines()
        formula_content = [x.rstrip() for x in formula_content]
    return formula_path, formula_content

def modify_url(formula_content):
    for line_no, line_contents in enumerate(formula_content):
        # Find/replace first url
        if 'url' in line_contents:
            formula_content[line_no] = '  url "' + UPSTREAM_URL + '"'
            break

def modify_sha256(formula_content):
    tmp_file = tempfile.mkstemp()[1]
    response = urlopen(UPSTREAM_URL)
    with open(tmp_file, 'wb') as f:
        f.write(response.read())
    sha256 = hashlib.sha256()
    with open(tmp_file, 'rb') as f:
        sha256.update(f.read())
    computed_hash = sha256.hexdigest()
    for line_no, line_contents in enumerate(formula_content):
        # Find/replace first sha256
        if 'sha256' in line_contents:
            formula_content[line_no] = '  sha256 "' + computed_hash + '"'
            break

def _should_include_resource(r):
    return not r.startswith('azure-cli') and r not in ['futures']

def modify_resources(formula_content):
    start_resources_line_no = None
    end_resources_line_no = None
    for line_no, line_contents in enumerate(formula_content):
        if 'resource' in line_contents and start_resources_line_no is None:
            start_resources_line_no = line_no
        if 'def install' in line_contents and end_resources_line_no is None:
            end_resources_line_no = line_no - 1
            break
    # Delete resources block
    del formula_content[start_resources_line_no : end_resources_line_no]
    # The script will have installed homebrew-pypi-poet by this point so we can import
    from poet.poet import make_graph, RESOURCE_TEMPLATE
    nodes = make_graph('azure-cli')
    filtered_nodes = OrderedDict([(n, nodes[n]) for n in nodes if _should_include_resource(n)])
    resources_stanza = '\n\n'.join([RESOURCE_TEMPLATE.render(resource=node) for node in filtered_nodes.values()])
    formula_content[start_resources_line_no:start_resources_line_no] = resources_stanza.split('\n')


def write_file(formula_path, formula_content):
    with open(formula_path, 'w') as f:
        for line in formula_content:
            f.write("%s\n" % line)

def setup_pip_deps():
    pip(['install', '--ignore-installed', 'azure-cli', 'homebrew-pypi-poet'], _out=sys.stdout, _err=sys.stdout)

def main():
    formula_path, formula_content = get_homebrew_formula()
    setup_pip_deps()
    modify_url(formula_content)
    modify_sha256(formula_content)
    modify_resources(formula_content)
    write_file(formula_path, formula_content)
    print('Done')
    new_formula_path = formula_path
    if BUILD_ARTIFACTS_DIR:
        new_formula_path = os.path.join(BUILD_ARTIFACTS_DIR, 'azure-cli.rb')
        shutil.copyfile(formula_path, new_formula_path)
    print('The new Homebrew formula is available at {}'.format(new_formula_path))
    print('Create a PR to {} for {}'.format(HOMEBREW_REPO_URL, AZURE_CLI_FORMULA_PATH))


if __name__ == '__main__':
    main()
