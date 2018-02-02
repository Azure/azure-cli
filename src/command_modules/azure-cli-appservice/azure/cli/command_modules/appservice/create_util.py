# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import zipfile
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.cli.command_modules.resource._client_factory import (
    _resource_client_factory)
from ._client_factory import web_client_factory


def zip_contents_from_dir(dirPath):
    relroot = os.path.abspath(os.path.join(dirPath, os.pardir))
    path_and_file = os.path.splitdrive(dirPath)[1]
    file = os.path.split(path_and_file)[1]
    zip_file_path = relroot + "\\" + file + ".zip"
    abs_src = os.path.abspath(dirPath)
    with zipfile.ZipFile("{}".format(zip_file_path), "w", zipfile.ZIP_DEFLATED) as zf:
        for dirname, subdirs, files in os.walk(dirPath):
            # skip node_modules folder for Node apps, since zip_deployment will perfom the build operation
            if 'node_modules' in subdirs:
                subdirs.remove('node_modules')
            for filename in files:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                zf.write(absname, arcname)
    return zip_file_path


def is_node_application(path):
    # for node application, package.json should exisit in the application root dir
    # if this exists we pass the path of the file to read it contents & get version
    package_json_file = os.path.join(path, 'package.json')
    if os.path.isfile(package_json_file):
        return package_json_file
    return ''


def get_node_runtime_version_toSet(node_version):
    version_val = "8.0"
    trunc_version = float(node_version[:3])
    # TODO: call the list_runtimes once there is an API that returs the supported versions
    if (trunc_version == 4.5 or trunc_version == 4.4 or trunc_version == 6.2 or
            trunc_version == 6.6 or trunc_version == 6.9 or trunc_version == 6.10 or
            trunc_version == 6.11 or trunc_version == 8.0 or trunc_version == 8.1):
        return node_version
    return version_val


def create_resource_group(cmd, rg_name, location):
    rcf = _resource_client_factory(cmd.cli_ctx)
    rg_params = ResourceGroup(location=location)
    return rcf.resource_groups.create_or_update(rg_name, rg_params)


def check_resource_group_exists(cmd, rg_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.resource_groups.check_existence(rg_name)


def check_resource_group_supports_linux(cmd, rg_name, location):
    # get all appservice plans from RG
    client = web_client_factory(cmd.cli_ctx)
    plans = list(client.app_service_plans.list_by_resource_group(rg_name))
    # filter by location & reserverd=false
    for item in plans:
        if item.location == location and not item.reserved:
            return False
    return True


def check_if_asp_exists(cmd, rg_name, asp_name):
    # get all appservice plans from RG
    client = web_client_factory(cmd.cli_ctx)
    for item in list(client.app_service_plans.list_by_resource_group(rg_name)):
        if item.name == asp_name:
            return True
    return False
