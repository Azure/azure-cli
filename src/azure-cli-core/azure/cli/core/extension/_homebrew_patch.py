# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import sys

from knack.log import get_logger

logger = get_logger(__name__)


HOMEBREW_CELLAR_PATH = '/usr/local/Cellar/azure-cli/'


def is_homebrew():
    return any((p.startswith(HOMEBREW_CELLAR_PATH) for p in sys.path))


# A workaround for https://github.com/Azure/azure-cli/issues/4428
class HomebrewPipPatch:  # pylint: disable=too-few-public-methods

    CFG_FILE = os.path.expanduser(os.path.join('~', '.pydistutils.cfg'))

    def __init__(self):
        self.our_cfg_file = False

    def __enter__(self):
        if not is_homebrew():
            return
        if os.path.isfile(HomebrewPipPatch.CFG_FILE):
            logger.debug("Homebrew patch: The file %s already exists and we will not overwrite it. "
                         "If extension installation fails, temporarily rename this file and try again.",
                         HomebrewPipPatch.CFG_FILE)
            logger.warning("Unable to apply Homebrew patch for extension installation. "
                           "Attempting to continue anyway...")
            self.our_cfg_file = False
        else:
            logger.debug("Homebrew patch: Temporarily creating %s to support extension installation on Homebrew.",
                         HomebrewPipPatch.CFG_FILE)
            with open(HomebrewPipPatch.CFG_FILE, "w") as f:
                f.write("[install]\nprefix=")
            self.our_cfg_file = True

    def __exit__(self, exc_type, exc_value, tb):
        if not is_homebrew():
            return
        if self.our_cfg_file and os.path.isfile(HomebrewPipPatch.CFG_FILE):
            logger.debug("Homebrew patch: Deleting the temporarily created %s", HomebrewPipPatch.CFG_FILE)
            os.remove(HomebrewPipPatch.CFG_FILE)
