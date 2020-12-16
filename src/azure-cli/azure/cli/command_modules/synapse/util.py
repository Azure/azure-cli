# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from .constant import SPARK_DOTNET_ASSEMBLY_SEARCH_PATHS_KEY, SPARK_DOTNET_UDFS_FOLDER_NAME


def categorized_files(reference_files):
    files = []
    jars = []
    for file in reference_files:
        file = file.strip()
        if file.endswith(".jar"):
            jars.append(file)
        else:
            files.append(file)
    return files, jars


def check_udfs_folder(conf):
    paths = conf.get(SPARK_DOTNET_ASSEMBLY_SEARCH_PATHS_KEY, '').split(',')
    paths = [path for path in paths if path != '']
    udfs_folder_name = './{}'.format(SPARK_DOTNET_UDFS_FOLDER_NAME)
    if udfs_folder_name not in paths:
        paths.append(udfs_folder_name)
    conf[SPARK_DOTNET_ASSEMBLY_SEARCH_PATHS_KEY] = ','.join(paths)


def get_tenant_id():
    from azure.cli.core._profile import Profile
    profile = Profile()
    sub = profile.get_subscription()
    tenant_id = sub['tenantId']
    return tenant_id
