# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class EventCounts(Model):
    """EventCounts.

    :param average_rating: Average rating on the day for extension
    :type average_rating: int
    :param buy_count: Number of times the extension was bought in hosted scenario (applies only to VSTS extensions)
    :type buy_count: int
    :param connected_buy_count: Number of times the extension was bought in connected scenario (applies only to VSTS extensions)
    :type connected_buy_count: int
    :param connected_install_count: Number of times the extension was installed in connected scenario (applies only to VSTS extensions)
    :type connected_install_count: int
    :param install_count: Number of times the extension was installed
    :type install_count: long
    :param try_count: Number of times the extension was installed as a trial (applies only to VSTS extensions)
    :type try_count: int
    :param uninstall_count: Number of times the extension was uninstalled (applies only to VSTS extensions)
    :type uninstall_count: int
    :param web_download_count: Number of times the extension was downloaded (applies to VSTS extensions and VSCode marketplace click installs)
    :type web_download_count: long
    :param web_page_views: Number of detail page views
    :type web_page_views: long
    """

    _attribute_map = {
        'average_rating': {'key': 'averageRating', 'type': 'int'},
        'buy_count': {'key': 'buyCount', 'type': 'int'},
        'connected_buy_count': {'key': 'connectedBuyCount', 'type': 'int'},
        'connected_install_count': {'key': 'connectedInstallCount', 'type': 'int'},
        'install_count': {'key': 'installCount', 'type': 'long'},
        'try_count': {'key': 'tryCount', 'type': 'int'},
        'uninstall_count': {'key': 'uninstallCount', 'type': 'int'},
        'web_download_count': {'key': 'webDownloadCount', 'type': 'long'},
        'web_page_views': {'key': 'webPageViews', 'type': 'long'}
    }

    def __init__(self, average_rating=None, buy_count=None, connected_buy_count=None, connected_install_count=None, install_count=None, try_count=None, uninstall_count=None, web_download_count=None, web_page_views=None):
        super(EventCounts, self).__init__()
        self.average_rating = average_rating
        self.buy_count = buy_count
        self.connected_buy_count = connected_buy_count
        self.connected_install_count = connected_install_count
        self.install_count = install_count
        self.try_count = try_count
        self.uninstall_count = uninstall_count
        self.web_download_count = web_download_count
        self.web_page_views = web_page_views
