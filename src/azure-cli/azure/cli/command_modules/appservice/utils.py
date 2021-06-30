# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from knack.util import CLIError
from azure.cli.core.azclierror import (RequiredArgumentMissingError)


def str2bool(v):
    if v == 'true':
        retval = True
    elif v == 'false':
        retval = False
    else:
        retval = None
    return retval


def _normalize_sku(sku):
    sku = sku.upper()
    if sku == 'FREE':
        return 'F1'
    if sku == 'SHARED':
        return 'D1'
    return sku


def get_sku_name(tier):  # pylint: disable=too-many-return-statements
    tier = tier.upper()
    if tier in ['F1', 'FREE']:
        return 'FREE'
    if tier in ['D1', "SHARED"]:
        return 'SHARED'
    if tier in ['B1', 'B2', 'B3', 'BASIC']:
        return 'BASIC'
    if tier in ['S1', 'S2', 'S3']:
        return 'STANDARD'
    if tier in ['P1', 'P2', 'P3']:
        return 'PREMIUM'
    if tier in ['P1V2', 'P2V2', 'P3V2']:
        return 'PREMIUMV2'
    if tier in ['P1V3', 'P2V3', 'P3V3']:
        return 'PREMIUMV3'
    if tier in ['PC2', 'PC3', 'PC4']:
        return 'PremiumContainer'
    if tier in ['EP1', 'EP2', 'EP3']:
        return 'ElasticPremium'
    if tier in ['I1', 'I2', 'I3']:
        return 'Isolated'
    if tier in ['I1V2', 'I2V2', 'I3V2']:
        return 'IsolatedV2'
    raise CLIError("Invalid sku(pricing tier), please refer to command help for valid values")


def normalize_sku_for_staticapp(sku):
    if sku.lower() == 'free':
        return 'Free'
    if sku.lower() == 'standard':
        return 'Standard'
    raise CLIError("Invalid sku(pricing tier), please refer to command help for valid values")


def retryable_method(retries=3, interval_sec=5, excpt_type=Exception):
    def decorate(func):
        def call(*args, **kwargs):
            current_retry = retries
            while True:
                try:
                    return func(*args, **kwargs)
                except excpt_type as exception:  # pylint: disable=broad-except
                    current_retry -= 1
                    if current_retry <= 0:
                        raise exception
                time.sleep(interval_sec)
        return call
    return decorate


def raise_missing_token_suggestion():
    pat_documentation = "https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line"
    raise RequiredArgumentMissingError("GitHub access token is required to authenticate to your repositories. "
                                       "If you need to create a Github Personal Access Token, "
                                       "please run with the '--login-with-github' flag or follow "
                                       "the steps found at the following link:\n{0}".format(pat_documentation))
