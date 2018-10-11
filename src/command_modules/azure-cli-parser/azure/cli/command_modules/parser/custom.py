# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
import yaml


logger = get_logger(__name__)


def parse_yaml(file_name, as_yaml=False):

    try:
        f = open(file_name)
    except IOError as e:
        raise CLIError("Error: {}".format(e))

    contents = f.read()

    try:
        contents = yaml.load(contents)
    except yaml.YAMLError as e:
        raise CLIError("Error: {}".format(e))

    if as_yaml:
        print(yaml.dump(contents, default_flow_style=False))
        return None

    return contents
