from typing import Dict, List, Tuple

from tox.report import setup_report

from .parser import Handler, Parsed, ToxParser


def get_options(*args) -> Tuple[Parsed, List[str], Dict[str, Handler]]:
    guess_verbosity = _get_base(args)
    handlers, parsed, unknown = _get_core(args)
    if guess_verbosity != parsed.verbosity:
        setup_report(parsed.verbosity)  # pragma: no cover
    return parsed, unknown, handlers


def _get_base(args):
    tox_parser = ToxParser.base()
    parsed, unknown = tox_parser.parse(args)
    guess_verbosity = parsed.verbosity
    setup_report(guess_verbosity)
    return guess_verbosity


def _get_core(args):
    tox_parser = _get_core_parser()
    parsed, unknown = tox_parser.parse(args)
    handlers = {k: p for k, (_, p) in tox_parser.handlers.items()}
    return handlers, parsed, unknown


def _get_core_parser():
    tox_parser = ToxParser.core()
    # noinspection PyUnresolvedReferences
    from tox.plugin.manager import MANAGER

    MANAGER.tox_add_option(tox_parser)
    tox_parser.fix_defaults()
    return tox_parser
