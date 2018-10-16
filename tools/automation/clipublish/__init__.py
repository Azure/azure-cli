# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import requests

PUBLISH_TYPES = ['debian', 'rpm']


def get_debian_payload(cli_version, repo_id, distro, source_url):
    return {'name': 'azure-cli', 'version': cli_version + '-1~' + distro, 'repositoryId': repo_id, 'sourceUrl': source_url}


def get_yum_payload(cli_version, repo_id, source_url):
    return {'name': 'azure-cli', 'version': cli_version, 'repositoryId': repo_id, 'sourceUrl': source_url}


def publish_payload(endpoint, payload):
    assert 'REPO_PASSWORD' in os.environ, "Set REPO_PASSWORD environment variable"
    repo_password = os.environ['REPO_PASSWORD']
    repo_username = 'azure-cli'
    print('Publishing - {}'.format(payload))
    r = requests.post(endpoint + '/v1/packages', verify=False, auth=(repo_username, repo_password), json=payload)
    print('Status Code {}'.format(r.status_code))
    # Query with a GET to the following (creds. required)
    if r.status_code == 202:
        print(endpoint + r.headers['Location'])
    else:
        print('Possible error. Server didn\'t return 202 Accepted.')


def cli_publish(args):
    publish_type = args.publish_type
    cli_version = args.cli_version
    endpoint = args.endpoint
    if publish_type == 'debian':
        debs = args.debs
        assert debs, "No debs provided. Nothing to do."
        payloads = [get_debian_payload(cli_version, repo_id, distro, source_url) for repo_id, distro, source_url in debs]
        print('Payloads')
        print('\n'.join(str(p) for p in payloads))
        input('Please enter to confirm the payloads to make requests to publish the DEBIAN packages: ')
        for p in payloads:
            publish_payload(endpoint, p)
    elif publish_type == 'rpm':
        repo_id = args.rpm_repo_id
        source_url = args.rpm_source_url
        assert repo_id, "Missing --repo-id"
        assert source_url, "Missing --source-url"
        payload = get_yum_payload(cli_version, repo_id, source_url)
        print('Payload')
        print(payload)
        input('Please enter to confirm the payload to make requests to publish the RPM package: ')
        publish_payload(endpoint, payload)
    else:
        raise ValueError("Unknown publish type {}".format(publish_type))


def type_debs(val):
    repo_id, distro, source_url = val.split('/', 2)
    return repo_id, distro, source_url


def init_args(root):
    parser = root.add_parser('publish', help='Publish the CLI.')
    parser.set_defaults(func=cli_publish)
    git_args = parser.add_argument_group('Git Clone Arguments')
    parser.add_argument('-t', '--type', dest='publish_type', required=True,
                                  choices=PUBLISH_TYPES,
                                  help="Space separated list of the artifacts to build. Use '*' for all.")
    parser.add_argument('-c', '--cli-version', dest='cli_version', required=True,
                                  help="The version of the publish.")
    parser.add_argument('-e', '--repo-endpoint', dest='endpoint', required=True,
                                  help="The endpoint to publish the debian or yum package.")
    deb_args = parser.add_argument_group('Debian Publish Arguments')
    deb_args.add_argument('--debs', dest='debs', nargs='+', type=type_debs, default=[],
                               help='A space separated list of repoid/distro/source_url for each package to publish.')
    rpm_args = parser.add_argument_group('RPM Publish Arguments')
    rpm_args.add_argument('-r', '--rpm-repo-id', dest='rpm_repo_id', help='Repo ID for RPM Repo')
    rpm_args.add_argument('-s', '--rpm-source-url', dest='rpm_source_url', help='URL to the RPM package')
