# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib

models_module = importlib.import_module('azure.mgmt.media.models')

sdk_mes_formats_mapper = {'MP4Format':'Mp4Format',
                          'JpgFormat':'JpgFormat',
                          'PngFormat':'PngFormat',
                          'TransportStreamFormat':'TransportStreamFormat'}

def map_format_type(format_type):
    return sdk_mes_formats_mapper.get(format_type, format_type)
