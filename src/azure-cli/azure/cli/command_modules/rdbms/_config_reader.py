# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from azure.cli.core.azclierror import BadRequestError

_config = None


def get_config_json():
    global _config  # pylint:disable=global-statement
    if _config is not None:
        return _config
    with open("src\\azure-cli\\azure\\cli\\command_modules\\rdbms\\config.json", "r") as f:
        try:
            _config = json.load(f)
            return _config
        except ValueError as _:
            raise BadRequestError("Invalid json file. Make sure that the json file content is properly formatted.")


def get_cloud(cmd):
    config = get_config_json()
    return config[cmd.cli_ctx.cloud.name]


def get_cloud_cluster(cmd, location, subscription_id):
    cloud = get_cloud(cmd)
    try:
        clusters = cloud[location]
    except:
        clusters = None
    if clusters is not None:
        for cluster in clusters:
            if cloud[cluster] is not None:
                if subscription_id in cloud[cluster]["subscriptions"]:
                    return cloud[cluster]
    return
