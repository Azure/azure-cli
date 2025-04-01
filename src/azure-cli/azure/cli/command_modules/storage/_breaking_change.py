# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_other_breaking_change

register_other_breaking_change('storage account migration start',
                               message='Starting from version 2.73.0, changing redundancy configuration would require '
                                       'additional (y/n) confirmation: "After your request to convert the account’s '
                                       'redundancy configuration is validated, the conversion will typically complete '
                                       'in a few days, but can take several weeks depending on current resource '
                                       'demands in the region, account size, and other factors. '
                                       'The conversion can’t be stopped after being initiated, and for accounts with '
                                       'geo redundancy a failover can’t be initiated while conversion is in progress. '
                                       'The data within the storage account will continue to be accessible with no '
                                       'loss of durability or availability. '
                                       'Confirm redundancy configuration change: (y/n)"',
                               target_version='2.73.0')
