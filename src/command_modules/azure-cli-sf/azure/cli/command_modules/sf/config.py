# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
from azure.cli.core._environment import get_config_dir
from azure.cli.core._config import AzConfig
from azure.cli.core.util import CLIError


class SfConfigParser(object):
    def __init__(self, config_path=None):
        if not config_path:
            config_path = os.path.join(get_config_dir(), "config")
        self.az_config = AzConfig()
        self.az_config.config_parser.read(config_path)

    def no_verify_setting(self):
        return self.az_config.get("servicefabric", "no_verify", fallback="False") == "True"

    def ca_cert_info(self):
        using_ca = self.az_config.get("servicefabric", "use_ca", fallback="False")
        if using_ca == "True":
            return self.az_config.get("servicefabric", "ca_path", fallback=None)
        return None

    def connection_endpoint(self):
        return self.az_config.get("servicefabric", "endpoint", fallback=None)

    def cert_info(self):
        security_type = str(self.az_config.get("servicefabric", "security", fallback=""))
        if security_type == "pem":
            return self.az_config.get("servicefabric", "pem_path", fallback=None)
        elif security_type == "cert":
            cert_path = self.az_config.get("servicefabric", "cert_path", fallback=None)
            key_path = self.az_config.get("servicefabric", "key_path", fallback=None)
            return cert_path, key_path
        elif security_type == "none":
            return None
        else:
            raise CLIError("Cluster security type not set")
