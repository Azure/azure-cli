# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
try:
    from urllib.parse import urlparse, urlsplit
except ImportError:
    from urlparse import urlparse, urlsplit # pylint: disable=import-error

def validate_deployment_name(namespace):
    #If missing,try come out with a name associated with the template name
    if namespace.deployment_name is None:
        template_filename = None
        if namespace.template_file and os.path.isfile(namespace.template_file):
            template_filename = namespace.template_file
        if namespace.template_uri and urlparse(namespace.template_uri).scheme:
            template_filename = urlsplit(namespace.template_uri).path
        if template_filename:
            template_filename = os.path.basename(template_filename)
            namespace.deployment_name = os.path.splitext(template_filename)[0]
        else:
            namespace.deployment_name = 'deployment1'
