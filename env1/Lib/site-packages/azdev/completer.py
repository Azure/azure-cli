# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


# TODO: import from Knack once it is moved
# pylint: disable=too-few-public-methods
class Completer(object):

    def __init__(self, func):
        self.func = func

    def __call__(self, **kwargs):
        namespace = kwargs['parsed_args']
        prefix = kwargs['prefix']
        cmd = namespace._cmd  # pylint: disable=protected-access
        return self.func(cmd, prefix, namespace)


@Completer
def get_test_completion(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    # TODO: return the list of keys from the index
    return ['storage', 'network', 'redis']
