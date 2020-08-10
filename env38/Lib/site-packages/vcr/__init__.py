import logging
from .config import VCR
from logging import NullHandler
from .record_mode import RecordMode as mode  # noqa import is not used in this file

__version__ = "4.1.0"

logging.getLogger(__name__).addHandler(NullHandler())


default_vcr = VCR()
use_cassette = default_vcr.use_cassette
