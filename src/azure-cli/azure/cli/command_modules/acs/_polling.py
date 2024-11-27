# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Dict

from azure.core.polling.base_polling import LocationPolling, _is_empty, BadResponse, _as_json


class RunCommandLocationPolling(LocationPolling):
    """Extends LocationPolling but uses the body content instead of the status code for the status"""

    @staticmethod
    def _get_provisioning_state(response):
        """Attempt to get provisioning state from resource.

        :param azure.core.pipeline.transport.HttpResponse response: latest REST call response.
        :returns: Status if found, else 'None'.
        """
        if _is_empty(response):
            return None
        body: Dict = _as_json(response)
        return body.get("properties", {}).get("provisioningState")

    def get_status(self, pipeline_response):
        """Process the latest status update retrieved from the same URL as
        the previous request.

        :param azure.core.pipeline.PipelineResponse response: latest REST call response.
        :raises: BadResponse if status not 200 or 204.
        """
        response = pipeline_response.http_response
        if _is_empty(response):
            raise BadResponse(
                "The response from long running operation does not contain a body."
            )

        status = self._get_provisioning_state(response)
        return status or "Unknown"
