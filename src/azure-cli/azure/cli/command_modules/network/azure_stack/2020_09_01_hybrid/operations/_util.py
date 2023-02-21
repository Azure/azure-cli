# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import importlib


def import_aaz_by_profile(module_name):
    return importlib.import_module(f"azure.cli.command_modules.network.aaz.2020_09_01_hybrid.{module_name}")
