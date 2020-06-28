# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionEventCallbackCollection(Model):
    """ExtensionEventCallbackCollection.

    :param post_disable: Optional.  Defines an endpoint that gets called via a POST reqeust to notify that an extension disable has occurred.
    :type post_disable: :class:`ExtensionEventCallback <extension-management.v4_1.models.ExtensionEventCallback>`
    :param post_enable: Optional.  Defines an endpoint that gets called via a POST reqeust to notify that an extension enable has occurred.
    :type post_enable: :class:`ExtensionEventCallback <extension-management.v4_1.models.ExtensionEventCallback>`
    :param post_install: Optional.  Defines an endpoint that gets called via a POST reqeust to notify that an extension install has completed.
    :type post_install: :class:`ExtensionEventCallback <extension-management.v4_1.models.ExtensionEventCallback>`
    :param post_uninstall: Optional.  Defines an endpoint that gets called via a POST reqeust to notify that an extension uninstall has occurred.
    :type post_uninstall: :class:`ExtensionEventCallback <extension-management.v4_1.models.ExtensionEventCallback>`
    :param post_update: Optional.  Defines an endpoint that gets called via a POST reqeust to notify that an extension update has occurred.
    :type post_update: :class:`ExtensionEventCallback <extension-management.v4_1.models.ExtensionEventCallback>`
    :param pre_install: Optional.  Defines an endpoint that gets called via a POST reqeust to notify that an extension install is about to occur.  Response indicates whether to proceed or abort.
    :type pre_install: :class:`ExtensionEventCallback <extension-management.v4_1.models.ExtensionEventCallback>`
    :param version_check: For multi-version extensions, defines an endpoint that gets called via an OPTIONS request to determine the particular version of the extension to be used
    :type version_check: :class:`ExtensionEventCallback <extension-management.v4_1.models.ExtensionEventCallback>`
    """

    _attribute_map = {
        'post_disable': {'key': 'postDisable', 'type': 'ExtensionEventCallback'},
        'post_enable': {'key': 'postEnable', 'type': 'ExtensionEventCallback'},
        'post_install': {'key': 'postInstall', 'type': 'ExtensionEventCallback'},
        'post_uninstall': {'key': 'postUninstall', 'type': 'ExtensionEventCallback'},
        'post_update': {'key': 'postUpdate', 'type': 'ExtensionEventCallback'},
        'pre_install': {'key': 'preInstall', 'type': 'ExtensionEventCallback'},
        'version_check': {'key': 'versionCheck', 'type': 'ExtensionEventCallback'}
    }

    def __init__(self, post_disable=None, post_enable=None, post_install=None, post_uninstall=None, post_update=None, pre_install=None, version_check=None):
        super(ExtensionEventCallbackCollection, self).__init__()
        self.post_disable = post_disable
        self.post_enable = post_enable
        self.post_install = post_install
        self.post_uninstall = post_uninstall
        self.post_update = post_update
        self.pre_install = pre_install
        self.version_check = version_check
