# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._configuration import AzureRedHatOpenShiftClientConfiguration
from ._azure_red_hat_open_shift_client import AzureRedHatOpenShiftClient
__all__ = ['AzureRedHatOpenShiftClient', 'AzureRedHatOpenShiftClientConfiguration']

from .version import VERSION

__version__ = VERSION

