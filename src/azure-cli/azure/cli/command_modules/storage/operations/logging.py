# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def disable_logging(client, timeout=None):
    for s in client:
        s.disable_logging(timeout=timeout)


def set_logging(client, log, retention, timeout=None, version=None):
    for s in client:
        s.set_logging('r' in log, 'w' in log, 'd' in log, retention, timeout=timeout, version=version)


def get_logging(client, timeout=None):
    from azure.common import AzureException
    from knack.util import CLIError
    results = {}
    for s in client:
        try:
            results[s.name] = s.get_logging(timeout)
        except KeyError:
            raise CLIError("Your storage account doesn't support logging for {} service. Please change value for "
                           "--services in your commands.".format(s.name))
        except AzureException as ex:
            # pylint: disable = no-member
            if ex.args and isinstance(ex.args, tuple) and hasattr(ex.args[0], 'args') and ex.args[0].args \
                    and 'Max retries exceeded with url: /?restype=service&comp=properties' in ex.args[0].args[0]:
                raise CLIError("Your storage account doesn't support logging for {} service. Please change value for "
                               "--services in your commands.".format(s.name))
            raise ex

    return results
