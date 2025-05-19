# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#

import unittest

from msrest.exceptions import ClientRequestError, ValidationError
from azure.cli.command_modules.batch._exception_handler import batch_exception_handler
from azure.core.exceptions import (
    HttpResponseError,
    ResourceNotFoundError
)
from azure.batch.models import BatchError, BatchErrorMessage, BatchErrorDetail
from azure.cli.core.azclierror import (
    AzureInternalError,
    BadRequestError,
    ClientRequestError as AzCliClientRequestError,
    ForbiddenError,
    ResourceNotFoundError as AzCliResourceNotFoundError,
    UnauthorizedError,
    ValidationError as AzCliValidationError,
)

from json import JSONDecodeError


class TestBatchExceptionHandler(unittest.TestCase):

    def test_non_batch_err(self):
        err = ValueError("Not a Batch error")
        with self.assertRaisesRegex(ValueError, r"^Not a Batch error$"):
            batch_exception_handler(err)
    
    def test_response_err(self):
        err = batch_err(500, HttpResponseError, "Kaboom")
        with self.assertRaisesRegex(AzureInternalError, r"^Kaboom$"):
            batch_exception_handler(err)

    def test_response_err_empty_model(self):
        err = batch_err(500, HttpResponseError, "Kaboom",
                        model=BatchError())
        with self.assertRaisesRegex(AzureInternalError, r"^Kaboom$"):
            batch_exception_handler(err)

    def test_response_err_code_only(self):
        err = batch_err(504, HttpResponseError, "Kaboom",
                        model=BatchError(code="explosion"))
        with self.assertRaisesRegex(AzureInternalError, r"^\(explosion\)$"):
            batch_exception_handler(err)

    def test_response_err_json_parsing_err(self):
        err = batch_err(404, ResourceNotFoundError, "Kaboom",
                        model=BatchError(code="explosion"),
                        raise_parsing_err=True)
        # No code displayed because JSON parsing failed
        with self.assertRaisesRegex(AzCliResourceNotFoundError, r"^Kaboom$"):
            batch_exception_handler(err)

    def test_response_err_msg_and_code(self):
        err = batch_err(501, HttpResponseError, "Kaboom",
                        model=BatchError(code="explosion", message=BatchErrorMessage(lang="en-us", value="Blew up")))
        with self.assertRaisesRegex(AzureInternalError, r"^\(explosion\) Blew up$"):
            batch_exception_handler(err)

    def test_bad_request_err(self):
        err = batch_err(400, HttpResponseError, "Kaboom",
                        model=BatchError(code="explosion", message=BatchErrorMessage(lang="en-us", value="Blew up")))
        with self.assertRaisesRegex(BadRequestError, r"^\(explosion\) Blew up$"):
            batch_exception_handler(err)

    def test_unauthorized_err(self):
        err = batch_err(401, HttpResponseError, "Kaboom",
                        model=BatchError(code="explosion", message=BatchErrorMessage(lang="en-us", value="Blew up")))
        with self.assertRaisesRegex(UnauthorizedError, r"^\(explosion\) Blew up$"):
            batch_exception_handler(err)

    def test_forbidden_err(self):
        err = batch_err(403, HttpResponseError, "Kaboom",
                        model=BatchError(code="explosion", message=BatchErrorMessage(lang="en-us", value="Blew up")))
        with self.assertRaisesRegex(ForbiddenError, r"^\(explosion\) Blew up$"):
            batch_exception_handler(err)
    
    def test_resource_not_found_err(self):
        err = batch_err(404, ResourceNotFoundError, "Kaboom",
                        model=BatchError(code="explosion", message=BatchErrorMessage(lang="en-us", value="Blew up")))
        with self.assertRaisesRegex(AzCliResourceNotFoundError, r"^\(explosion\) Blew up$"):
            batch_exception_handler(err)

    def test_validation_error(self):
        err = ValidationError("rule", "target", "value")
        try:
            batch_exception_handler(err)
        except AzCliValidationError as e:
            self.assertEqual(str(e), str(err))
    
    def test_client_request_error(self):
        err = ClientRequestError("Kaboom")
        try:
            batch_exception_handler(err)
        except AzCliClientRequestError as e:
            self.assertEqual(str(e), str(err))

    def test_response_err_details(self):
        err = HttpResponseError("Kaboom")

        err_details = []

        detail1 = BatchErrorDetail()
        detail1.key = "key1"
        detail1.value = "value1"
        err_details.append(detail1)

        detail2 = BatchErrorDetail()
        detail2.value = "value2"
        err_details.append(detail2)

        detail3 = BatchErrorDetail()
        detail3.key = "key3"
        err_details.append(detail3)

        detail4 = BatchErrorDetail()
        err_details.append(detail4)

        err = batch_err(500, HttpResponseError, "Kaboom", model=BatchError(
            code="explosion",
            message=BatchErrorMessage(lang="en-us", value="Blew up"),
            values_property=err_details))

        # Key/value should never be null in practice, but since they are marked Optional,
        # the error handler shouldn't fail on nulls.
        with self.assertRaises(AzureInternalError) as context:
            batch_exception_handler(err)

        self.assertEqual(str(context.exception), "(explosion) Blew up\nkey1: value1\nNone: value2\nkey3: None\nNone: None")


def batch_err(status_code, cls, message, model=None, json=None, raise_parsing_err=False):
    err = cls(message)
    err.status_code = status_code
    if model:
        err.model = model
        err.response = FakeResponse(model.as_dict(), raise_parsing_err)
    if json:
        err.response = FakeResponse(json, raise_parsing_err)
    return err


class FakeResponse:

    def __init__(self, response_json, raise_parsing_err=False):
        self._json = response_json
        self._raise_parsing_err = raise_parsing_err

    def json(self):
        if self._raise_parsing_err:
            raise JSONDecodeError("Fake JSON parsing error", "fake docs", 10)
        return self._json
