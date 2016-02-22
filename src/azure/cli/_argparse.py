from __future__ import print_function
import json
import os
import sys

from ._locale import get_file as locale_get_file
from ._logging import logger

# Named arguments are prefixed with one of these strings
ARG_PREFIXES = sorted(('-', '--', '/'), key=len, reverse=True)

# Values are separated from argument name with one or more of these characters
# or a space
ARG_SEPARATORS = ':='

class IncorrectUsageError(Exception):
    '''Raised when a command is incorrectly used and the usage should be
    displayed to the user.
    '''
    pass

class Arguments(dict):
    def __init__(self, source=None):
        self.positional = []
        if source:
            self.update(source)

    def add_from_dotted(self, key, value):
        d = self
        bits = key.split('.')
        for p in bits[:-1]:
            d = d.setdefault(p, Arguments())
            if not isinstance(d, Arguments):
                raise RuntimeError('incompatible arguments for "{}"'.format(p))
        d[bits[-1]] = value

    def __getattr__(self, key):
        try:
            return self[key]
        except LookupError:
            pass
        logger.debug('Argument %s is required', key)
        raise IncorrectUsageError(_("Argument {0} is required").format(key))

def _read_arg(string):
    for prefix in ARG_PREFIXES:
        if string.startswith(prefix):
            a1, a2 = string, None
            indices = sorted((a1.find(sep), sep) for sep in ARG_SEPARATORS)
            sep = next((i[1] for i in indices if i[0] > len(prefix)), None)
            if sep:
                a1, _, a2 = a1.partition(sep)
            return a1[len(prefix):].lower(), a2
    return None, None

def _index(string, char, default=sys.maxsize):
    try:
        return string.index(char)
    except ValueError:
        return default


class ArgumentParser(object):
    def __init__(self, prog):
        self.prog = prog
        self.noun_map = {
            '$doc': 'azure-cli.txt',
        }
        self.help_args = { '--help', '-h' }
        self.complete_args = { '--complete' }
        self.global_args = { '--verbose', '--debug' }

    def add_command(self, handler, name=None, description=None, args=None):
        '''Registers a command that may be parsed by this parser.

        `handler` is the function to call with two `Arguments` objects.
        All recognized arguments will appear on the first; all others on the
        second. Accessing a missing argument as an attribute will raise
        `IncorrectUsageError` that typically displays the command help.
        Accessing a missing argument as an index or using `get` behaves like a
        dictionary.

        `name` is a space-separated list of names identifying the command.

        `description` is a short piece of help text to display in usage info.

        `args` is a list of (spec, description) tuples. Each spec is either the
        name of a positional argument, or an ``'--argument -a <variable>'``
        string listing one or more argument names and an optional variable name.
        When multiple names are specified, the first is always used as the
        name on `Arguments`.
        '''
        nouns = (name or handler.__name__).split()
        full_name = ''
        m = self.noun_map
        for n in nouns:
            full_name += n
            m = m.setdefault(n.lower(), {
                '$doc': full_name + ".txt"
            })
            full_name += '.'
        m['$description'] = description or handler.__doc__
        m['$handler'] = handler

        m['$args'] = []
        m['$kwargs'] = kw = {}
        m['$argdoc'] = ad = []
        for spec, desc in (args or []):
            if not any(spec.startswith(p) for p in ARG_PREFIXES):
                m['$args'].append(spec.strip('<> '))
                ad.append((spec, desc))
                continue

            aliases = spec.split()
            if any(aliases[-1].startswith(p) for p in ARG_PREFIXES):
                v = True
            else:
                v = aliases.pop().strip('<> ')
            target, _ = _read_arg(aliases[0])
            kw.update({_read_arg(a)[0]: (target, v) for a in aliases})
            ad.append(('/'.join(aliases), desc))


    def execute(self, args, show_usage=False, show_completions=False, out=sys.stdout):
        '''Parses `args` and invokes the associated handler.

        The handler is passed two `Arguments` objects with all arguments other
        than those in `self.help_args`, `self.complete_args` and
        `self.global_args`. The first contains arguments that were defined by
        the handler spec, while the second contains all other arguments.

        If `show_usage` is ``True`` or any of `self.help_args` has been provided
        then usage information will be displayed instead of executing the
        command.

        If `show_completions` is ``True`` or any of `self.complete_args` has
        been provided then raw information about the likely arguments will be
        provided.
        '''
        if not show_usage:
            show_usage = any(a in self.help_args for a in args)
        if not show_completions:
            show_completions = any(a in self.complete_args for a in args)

        all_global_args = set(a.lstrip('-/') for a in self.help_args | self.complete_args | self.global_args)
        def not_global(a):
            return a.lstrip('-/') not in all_global_args
        it = filter(not_global, args)

        m = self.noun_map
        nouns = []
        n = next(it, '')
        while n:
            try:
                m = m[n.lower()]
                nouns.append(n.lower())
            except LookupError:
                if '$args' not in m:
                    show_usage = True
                break
            n = next(it, '')

        try:
            expected_args = m['$args']
            expected_kwargs = m['$kwargs']
            handler = m['$handler']
        except LookupError:
            logger.debug('Missing data for noun %s', n)
            show_usage = True
        
        if show_completions:
            return self._display_completions(nouns, m, args, out)
        if show_usage:
            return self._display_usage(nouns, m, args, out)

        parsed = Arguments()
        others = Arguments()
        while n:
            next_n = next(it, '')

            key_n, value = _read_arg(n)
            if key_n:
                target_value = expected_kwargs.get(key_n)
                if target_value is None:
                    # Unknown arg always takes an argument.
                    if value is None:
                        value, next_n = next_n, next(it, '')
                    others.add_from_dotted(key_n, value)
                elif target_value[1] is True:
                    # Arg with no value
                    if value is not None:
                        print(_("argument '{0}' does not take a value").format(key_n), file=out)
                        return self._display_usage(nouns, m, args, out)
                    parsed.add_from_dotted(target_value[0], True)
                else:
                    # Arg with a value
                    if value is None:
                        value, next_n = next_n, next(it, '')
                    parsed.add_from_dotted(target_value[0], value)
            else:
                # Positional arg
                parsed.positional.append(n)
            n = next_n

        old_stdout = sys.stdout
        try:
            sys.stdout = out
            return handler(parsed, others)
        except IncorrectUsageError as ex:
            print(str(ex), file=out)
            return self.display_usage(nouns, m, args, out)
        finally:
            sys.stdout = old_stdout

    def _display_usage(self, nouns, noun_map, arguments, out=sys.stdout):
        spec = ' '.join(noun_map.get('$spec') or nouns)
        print('    {} {}'.format(self.prog, spec), file=out)
        print(file=out, flush=True)
        
        subnouns = sorted(k for k in noun_map if not k.startswith('$'))
        if subnouns:
            print('Subcommands', file=out)
            for n in subnouns:
                print('    {}'.format(n), file=out)
            print(file=out, flush=True)
        
        argdoc = noun_map.get('$argdoc')
        if argdoc:
            print('Arguments', file=out)
            maxlen = max(len(a) for a, d in argdoc)
            for a, d in argdoc:
                print('    {0:<{1}} - {2}'.format(a, maxlen, d), file=out)
            print(file=out, flush=True)

        doc_file = locale_get_file(noun_map['$doc'])
        try:
            with open(doc_file, 'r') as f:
                print(f.read(), file=out, flush=True)
        except OSError:
            # TODO: Behave better when no docs available
            print('No documentation available', file=out, flush=True)
            logger.debug('Expected documentation at %s', doc_file)

    def _display_completions(self, nouns, noun_map, arguments, out=sys.stdout):
        completions = [k for k in noun_map if not k.startswith('$')]

        kwargs = noun_map.get('$kwargs')
        if kwargs:
            completions.extend('--' + a for a in kwargs if a)

        print('\n'.join(sorted(completions)), file=out, flush=True)
