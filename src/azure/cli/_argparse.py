from __future__ import print_function
import json
import logging
import os
import sys

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
        raise IncorrectUsageError(_("Argument {0} is required").format(key))

def _iter_args(args, skip):
    for a in args:
        a1, a2 = a, None
        if '=' in a1:
            a1, _, a2 = a1.partition('=')
        elif ':' in a1:
            a1, _, a2 = a1.partition(':')

        if a1 and a1 not in skip:
            yield a1
            if a2:
                yield a2


class ArgumentParser(object):
    def __init__(self, prog):
        self.prog = prog
        self.noun_map = {
            '$doc': 'azure-cli',
        }
        self.help_args = { '--help', '-h' }
        self.complete_args = { '--complete' }
        self.global_args = { '--verbose', '--debug' }

        self.doc_source = './'
        self.doc_suffix = '.txt'

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
                '$doc': full_name
            })
            full_name += '.'
        m['$description'] = description or handler.__doc__
        m['$handler'] = handler

        m['$args'] = []
        m['$kwargs'] = kw = {}
        m['$argdoc'] = ad = []
        for spec, desc in (args or []):
            if not spec.startswith('-'):
                m['$args'].append(spec.strip('<> '))
                ad.append((spec, desc))
                continue

            aliases = spec.split()
            target = aliases[0].strip('-')
            if aliases[-1].startswith('-'):
                v = True
            else:
                v = aliases.pop().strip('<> ')
            kw.update({a: (target, v) for a in aliases})
            ad.append(('/'.join(aliases), desc))

        # args are added in reverse order, so reverse our lists
        m['$args'].reverse()
        ad.reverse()


    def execute(self, args, show_usage=False, show_completions=False, out=sys.stdout):
        '''Parses `args` and invokes the associated handler.

        The handler is passed an `Arguments` object with all arguments other
        than those in `self.help_args`, `self.complete_args` and
        `self.global_args`.

        Arguments that are 

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

        all_global_args = self.help_args | self.complete_args | self.global_args
        it = _iter_args(args, all_global_args)

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
            show_usage = True
        
        if show_completions:
            return self._display_completions(nouns, m, args, out)
        if show_usage:
            return self._display_usage(nouns, m, args, out)

        parsed = Arguments()
        others = Arguments()
        while n:
            next_n = next(it, '')

            if n.startswith('-'):
                key_n = n.lower()
                target_value = expected_kwargs.get(key_n)
                key_n = key_n.strip('-')
                if target_value is None:
                    # Unknown arg
                    if next_n:
                        others.add_from_dotted(key_n, next_n)
                        next_n = next(it, '')
                    else:
                        others.add_from_dotted(key_n, True)
                elif target_value[1] is True:
                    # Arg with no value
                    parsed.add_from_dotted(target_value[0], True)
                else:
                    # Arg with a value
                    parsed.add_from_dotted(target_value[0], next_n)
                    next_n = next(it, '')
            else:
                # Positional arg
                parsed.positional.append(n)
            n = next_n

        try:
            return handler(parsed, others)
        except IncorrectUsageError as ex:
            print(str(ex), file=out)
            return self.display_usage(nouns, m, args, out)

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

        doc_file = os.path.join(self.doc_source, noun_map['$doc'] + self.doc_suffix)
        try:
            with open(doc_file, 'r') as f:
                print(f.read(), file=out, flush=True)
        except OSError:
            # TODO: Behave better when no docs available
            print('No documentation available', file=out, flush=True)
            logging.debug('Expected documentation at %s', doc_file)

    def _display_completions(self, nouns, noun_map, arguments, out=sys.stdout):
        completions = [k for k in noun_map if not k.startswith('$')]

        kwargs = noun_map.get('$kwargs')
        if kwargs:
            completions.extend('--' + a for a in kwargs if a)

        print('\n'.join(sorted(completions)), file=out, flush=True)
