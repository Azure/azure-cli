# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..base.base_manager import BaseManager

class ExtensionManager(BaseManager):
    """ Manage DevOps Extensions

    Install a new extension within an organization or view existing extensions.

    Attributes:
        See BaseManager
    """

    def __init__(self, organization_name="", creds=None):
        """Inits ExtensionManager as per BaseManager"""
        super(ExtensionManager, self).__init__(creds, organization_name=organization_name)

    def create_extension(self, extension_name, publisher_name):
        """Installs an extension in Azure DevOps if it does not already exist"""
        extensions = self.list_extensions()
        extension = next((extension for extension in extensions
                          if (extension.publisher_id == publisher_name)
                          and (extension.extension_id == extension_name)), None)
        # If the extension wasn't in the installed extensions than we know we need to install it
        if extension is None:
            extension = self._extension_management_client.install_extension_by_name(publisher_name, extension_name)

        return extension

    def list_extensions(self):
        """Lists an extensions already installed in Azure DevOps"""
        return self._extension_management_client.get_installed_extensions()
