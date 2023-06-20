# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from azure.cli.core.profiles import get_sdk, ResourceType

logger = get_logger(__name__)


def transform_file_directory_result(cli_ctx):
    """
    Transform a the result returned from file and directory listing API.
    This transformer add and remove properties from File and Directory objects in the given list
    in order to align the object's properties so as to offer a better view to the file and dir
    list.
    """
    def transformer(result):
        if getattr(result, 'next_marker', None):
            logger.warning('Next Marker:')
            logger.warning(result.next_marker)

        t_file, t_dir = get_sdk(cli_ctx, ResourceType.DATA_STORAGE, 'File', 'Directory', mod='file.models')
        return_list = []
        for each in result:
            if isinstance(each, t_file):
                delattr(each, 'content')
                setattr(each, 'type', 'file')
            elif isinstance(each, t_dir):
                setattr(each, 'type', 'dir')
            return_list.append(each)

        return return_list
    return transformer
