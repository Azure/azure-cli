# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)

DEFAULT_INDEX_URL = "https://aka.ms/azure-cli-extension-index-v1"

ERR_TMPL_EXT_INDEX = 'Unable to get extension index.\n'
ERR_TMPL_NON_200 = '{}Server returned status code {{}} for {{}}'.format(ERR_TMPL_EXT_INDEX)
ERR_TMPL_NO_NETWORK = '{}Please ensure you have network connection. Error detail: {{}}'.format(ERR_TMPL_EXT_INDEX)
ERR_TMPL_BAD_JSON = '{}Response body does not contain valid json. Error detail: {{}}'.format(ERR_TMPL_EXT_INDEX)

ERR_UNABLE_TO_GET_EXTENSIONS = 'Unable to get extensions from index. Improper index format.'
TRIES = 3


# pylint: disable=inconsistent-return-statements
def get_index(index_url=None):
    import requests
    from azure.cli.core.util import should_disable_connection_verify
    index_url = index_url or DEFAULT_INDEX_URL

    for try_number in range(TRIES):
        try:
            response = requests.get(index_url, verify=(not should_disable_connection_verify()))
            if response.status_code == 200:
                return response.json()
            msg = ERR_TMPL_NON_200.format(response.status_code, index_url)
            raise CLIError(msg)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
            msg = ERR_TMPL_NO_NETWORK.format(str(err))
            raise CLIError(msg)
        except ValueError as err:
            # Indicates that url is not redirecting properly to intended index url, we stop retrying after TRIES calls
            if try_number == TRIES - 1:
                msg = ERR_TMPL_BAD_JSON.format(str(err))
                raise CLIError(msg)
            import time
            time.sleep(0.5)
            continue


def get_index_extensions(index_url=None):
    index = get_index(index_url=index_url)
    extensions = index.get('extensions')
    if extensions is None:
        logger.warning(ERR_UNABLE_TO_GET_EXTENSIONS)
    return extensions
