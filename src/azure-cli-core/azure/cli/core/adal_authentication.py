# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests
import adal

from msrest.authentication import Authentication

from knack.util import CLIError
from azure.cli.core.util import in_cloud_console


class AdalAuthentication(Authentication):  # pylint: disable=too-few-public-methods

    def __init__(self, token_retriever, external_tenant_token_retriever=None):
        self._token_retriever = token_retriever
        self._external_tenant_token_retriever = external_tenant_token_retriever

    def signed_session(self, session=None):  # pylint: disable=arguments-differ
        session = session or super(AdalAuthentication, self).signed_session()
        external_tenant_tokens = None
        try:
            scheme, token, _ = self._token_retriever()
            if self._external_tenant_token_retriever:
                external_tenant_tokens = self._external_tenant_token_retriever()
        except CLIError as err:
            if in_cloud_console():
                AdalAuthentication._log_hostname()
            raise err
        except adal.AdalError as err:
            # pylint: disable=no-member
            if in_cloud_console():
                AdalAuthentication._log_hostname()
            if 'AADSTS70008:' in (getattr(err, 'error_response', None) or {}).get('error_description') or '':
                raise CLIError("Credentials have expired due to inactivity.{}".format(
                    " Please run 'az login'" if not in_cloud_console() else ''))

            raise CLIError(err)
        except requests.exceptions.ConnectionError as err:
            raise CLIError('Please ensure you have network connection. Error detail: ' + str(err))

        header = "{} {}".format(scheme, token)
        session.headers['Authorization'] = header
        if external_tenant_tokens:
            aux_tokens = ';'.join(['{} {}'.format(scheme2, tokens2) for scheme2, tokens2, _ in external_tenant_tokens])
            session.headers['x-ms-authorization-auxiliary'] = aux_tokens
        return session

    @staticmethod
    def _log_hostname():
        import socket
        from knack.log import get_logger
        logger = get_logger(__name__)
        logger.warning("A Cloud Shell credential problem occurred. When you report the issue with the error "
                       "below, please mention the hostname '%s'", socket.gethostname())
