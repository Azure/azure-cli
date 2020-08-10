# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


from azdev.utilities import (
    pip_cmd)


def install_draft_sdk(modules, private=False):
    for module in modules:
        kwargs = {
            'module': module,
            'pr': 'pr' if private else '',
            'branch': 'restapi_auto_{}/resource-manager'.format(module)
        }
        pip_cmd('install "git+https://github.com/Azure/azure-sdk-for-python{pr}@{branch}'
                '#egg=azure-mgmt-{module}&subdirectory=azure-mgmt-{module}"'.format(**kwargs),
                show_stderr=True,
                message='Installing draft SDK for azure-mgmt-{}...'.format(module))
