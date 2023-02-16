# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
import argparse
from ._exception_handler import CLIError


class AttestationEvidenceAddAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        result = {}
        evidence = getattr(namespace, self.dest)
        if evidence is None:
            evidence = []
        for item in values:
            try:
                key, value = item.split('=', 1)
                result[key] = value
            except ValueError:
                raise CLIError('usage error: {} KEY=VALUE [KEY=VALUE ...] {} {} {}'
                               .format(option_string, item, result, evidence))
        evidence.append(result)
        setattr(namespace, self.dest, evidence)
