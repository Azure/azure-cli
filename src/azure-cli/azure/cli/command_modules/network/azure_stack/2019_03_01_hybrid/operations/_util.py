# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import importlib


def import_aaz_by_profile(module_name):
    # use aaz in 2018-03-01-hybrid profile, because apis are the some.
    return importlib.import_module(f"azure.cli.command_modules.network.aaz.2018_03_01_hybrid.{module_name}")
