import unittest

from azure.cli.command_modules.batch._exception_handler import batch_exception_handler
from azure.core.exceptions import HttpResponseError
from azure.batch.models import BatchError, BatchErrorMessage, BatchErrorDetail

from knack.util import CLIError


class TestBatchExceptionHandler(unittest.TestCase):

    def test_response_err(self):
        err = HttpResponseError("Kaboom")
        with self.assertRaisesRegex(CLIError, r"^Kaboom$"):
            batch_exception_handler(err)
    
    def test_response_err_empty_model(self):
        err = HttpResponseError("Kaboom")
        err.model = BatchError()
        with self.assertRaisesRegex(CLIError, r"^Kaboom$"):
            batch_exception_handler(err)

    def test_response_err_code_only(self):
        err = HttpResponseError("Kaboom")
        err.model = BatchError(code="explosion")
        with self.assertRaisesRegex(CLIError, r"^\(explosion\)$"):
            batch_exception_handler(err)

    def test_response_err_msg_and_code(self):
        err = HttpResponseError("Kaboom")
        err.model = BatchError(code="explosion", message=BatchErrorMessage(lang="en-us", value="Blew up"))
        with self.assertRaisesRegex(CLIError, r"^\(explosion\) Blew up$"):
            batch_exception_handler(err)

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

        err.model = BatchError(
            code="explosion",
            message=BatchErrorMessage(lang="en-us", value="Blew up"),
            values_property=err_details)
        # Key/value should never be null in practice, but since they are marked Optional,
        # the error handler shouldn't fail on nulls.
        with self.assertRaises(CLIError) as context:
            batch_exception_handler(err)
        
        self.assertEquals(str(context.exception), "(explosion) Blew up\nkey1: value1\nNone: value2\nkey3: None\nNone: None")
