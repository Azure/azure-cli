# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.util import get_file_json
from azure.cli.core.parser import IncorrectUsageError

def list_cors(client, timeout=None):
    results = {}
    for s in client:
        results[s.name] = s.get_cors(timeout)
    return results


def add_cors(client, origins=None, methods=None, max_age=0, exposed_headers=None, allowed_headers=None, timeout=None,
             input_file=None):

    # TODO
    # Because if the storage command adds a validator in commands.py,
    # it will result in not executing validate_client_parameters,
    # which will miss the logic for querying storage connection parameters.
    # Therefore, the validator logic is temporarily written here and optimized before merge.
    if input_file is not None:
        if max_age:
            raise IncorrectUsageError("incorrect usage: "
                                      "'--input-file' and '--max-age' cannot be passed in at the same time")
        if origins:
            raise IncorrectUsageError("incorrect usage: "
                                      "'--input-file' and '--origins' cannot be passed in at the same time")
        if methods:
            raise IncorrectUsageError("incorrect usage: "
                                      "'--input-file' and '--methods' cannot be passed in at the same time")
        if allowed_headers:
            raise IncorrectUsageError("incorrect usage: "
                                      "'--input-file' and '--allowed-headers' cannot be passed in at the same time")
        if exposed_headers:
            raise IncorrectUsageError("incorrect usage: "
                                      "'--input-file' and '--exposed-headers' cannot be passed in at the same time")

        input_parameters = get_file_json(input_file, preserve_order=True)
        if 'origins' in input_parameters:
            origins = input_parameters['origins']
        if 'methods' in input_parameters:
            methods = input_parameters['methods']
        if 'exposed-headers' in input_parameters:
            exposed_headers = input_parameters['exposed-headers']
        if 'allowed-headers' in input_parameters:
            allowed_headers = input_parameters['allowed-headers']
        if 'max-age' in input_parameters and input_parameters['max-age'] is not None:
            max_age = str(input_parameters['max-age'])

    if origins is None:
        raise IncorrectUsageError("incorrect usage: "
                                  "Please pass in '--origins' or add origins parameter to the input-file")
    if methods is None:
        raise IncorrectUsageError("incorrect usage: "
                                  "Please pass in '--methods' or add methods parameter to the input-file")

    for s in client:
        s.add_cors(origins, methods, max_age, exposed_headers, allowed_headers, timeout)


def clear_cors(client, timeout=None):
    for s in client:
        s.clear_cors(timeout)
