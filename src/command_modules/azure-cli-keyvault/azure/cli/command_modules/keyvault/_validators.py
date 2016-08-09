#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse

# COMMAND NAMESPACE VALIDATORS

def process_policy_namespace(ns):
    # TODO Consider supporting mutual exclusion in CLI
    # https://docs.python.org/2/library/argparse.html#mutual-exclusion
    if sum(1 for p in [ns.object_id, ns.spn, ns.upn] if p) != 1:
        raise argparse.ArgumentError(
            None, 'One of the arguments --object-id --spn --upn is required')

def process_set_policy_perms_namespace(ns):
    if ns.perms_to_keys is None and ns.perms_to_secrets is None:
        raise argparse.ArgumentError(
            None, 'Specify at least --perms-to-keys or --perms-to-secrets.')

