from __future__ import print_function
import json
import logging
import os
import sys

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
        raise AttributeError(key)


def _split_argspec(spec):
    nouns, args, kwargs = [], [], {}
    it = iter(spec)
    n = next(it, None)
    while n:
        if n.startswith(('-', '<')):
            break
        nouns.append(n)
        n = next(it, None)

    while n:
        next_n = next(it, None)
        if n.startswith('-'):
            key_n = n.lower().strip('-')
            if next_n and not next_n.startswith('-'):
                kwargs[key_n] = next_n.strip('<> ')
                next_n = next(it, None)
            else:
                kwargs[key_n] = True
        else:
            args.append(n.strip('<> '))
        n = next_n

    return nouns, args, kwargs

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
    def __init__(self):
        self.noun_map = {
            '$doc': 'azure-cli',
        }
        self.help_args = { '--help', '-h' }
        self.complete_args = { '--complete' }
        self.global_args = { '--verbose', '--debug' }

        self.doc_source = './'
        self.doc_suffix = '.txt'

    def add_command(self, spec, handler):
        nouns, args, kwargs = _split_argspec(spec)
        full_name = ''
        m = self.noun_map
        for n in nouns:
            full_name += n
            m = m.setdefault(n.lower(), {
                '$doc': full_name
            })
            full_name += '.'
        m['$args'] = args
        m['$kwargs'] = kwargs
        m['$handler'] = handler

    def execute(self, args, out=sys.stdout):
        show_usage = any(a in self.help_args for a in args)
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
            return self.display_completions(nouns, m, args, out)
        if show_usage:
            return self.display_usage(nouns, m, args, out)

        parsed = Arguments()
        while n:
            next_n = next(it, '')

            key_n = n.lower().strip('-')
            expected_value = expected_kwargs.get(key_n)
            if expected_value is True:
                # Arg with no value
                parsed.add_from_dotted(key_n, True)
            elif not n.startswith('-'):
                # Positional arg
                parsed.positional.append(n)
            elif expected_value is not None or (next_n and not next_n.startswith('-')):
                # Arg with a value
                parsed.add_from_dotted(key_n, next_n)
                next_n = next(it, '')
            else:
                # Unknown arg
                parsed.add_from_dotted(key_n, True)
            n = next_n

        return handler(parsed)

    def display_usage(self, nouns, noun_map, arguments, out=sys.stdout):
        doc_file = os.path.join(self.doc_source, noun_map['$doc'] + self.doc_suffix)
        try:
            with open(doc_file, 'r') as f:
                print(f.read(), file=out, flush=True)
        except OSError:
            # TODO: Behave better when no docs available
            print('No documentation available', file=out, flush=True)
            logging.debug('Expected documentation at %s', doc_file)

    def display_completions(self, nouns, noun_map, arguments, out=sys.stdout):
        completions = [k for k in noun_map if not k.startswith('$')]

        kwargs = noun_map.get('$kwargs')
        if kwargs:
            completions.extend('--' + a for a in kwargs if a)

        print('\n'.join(sorted(completions)), file=out, flush=True)
