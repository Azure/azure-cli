from __future__ import print_function
import sys

from ._help import GroupHelpFile, CommandHelpFile, print_detailed_help, print_welcome_message
from ._locale import L
from ._logging import logger
from ._output import OutputProducer

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
    def __init__(self, source=None): #pylint: disable=super-init-not-called
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
        raise IncorrectUsageError(L('Argument {0} is required').format(key))

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

class ArgumentParserResult(object):  #pylint: disable=too-few-public-methods
    def __init__(self, result, output_format=None):
        self.result = result
        self.output_format = output_format

class ArgumentParser(object):
    def __init__(self, prog):
        self.prog = prog
        self.noun_map = {
            '$doc': 'azure-cli.txt',
        }
        self.help_args = {'--help', '-h'}
        self.complete_args = {'--complete'}
        self.global_args = {'--verbose', '--debug'}

    def add_command(self,
                    handler,
                    name=None,
                    description=None,
                    args=None):
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
        m['$description'] = description
        m['$handler'] = handler
        m['$doctext'] = handler.__doc__

        m['$args'] = []
        m['$kwargs'] = kw = {}
        m['$argdoc'] = ad = []
        for spec, desc, req, target in args or []:
            if not any(spec.startswith(p) for p in ARG_PREFIXES):
                m['$args'].append(spec.strip('<> '))
                ad.append((spec, desc, req))
                continue

            aliases = spec.split()
            if any(aliases[-1].startswith(p) for p in ARG_PREFIXES):
                v = True
            else:
                v = aliases.pop().strip('<> ')
            if not target:
                target, _ = _read_arg(aliases[0])
            kw.update({_read_arg(a)[0]: (target, v, req, aliases) for a in aliases})
            ad.append(('/'.join(aliases), desc, req))

    def execute(self,
                args,
                show_usage=False,
                show_completions=False,
                out=None):
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

        If `out` is not specified, we default to sys.stdout.
        '''
        out = sys.stdout if out is None else out

        if not show_usage:
            show_usage = any(a in self.help_args for a in args)
        if not show_completions:
            show_completions = any(a in self.complete_args for a in args)

        try:
            it = self._get_args_itr(args)
            m, n = self._get_noun_map(args, it, out)

            if show_usage:
                return ArgumentParserResult(self._display_usage(m, out))
            if show_completions:
                return ArgumentParserResult(
                    self._display_completions(m, args, out))

            if len(args) == 0:
                print_welcome_message(out)
                self._display_children(m, args, out)
                return ArgumentParserResult(None)

            expected_kwargs, handler = self._get_noun_data(m, n, args, out)

            others, parsed = self._parse_nouns(expected_kwargs, it, m, n, out)

            self._handle_required_args(expected_kwargs, parsed, out)

            output_format = self._get_output_format(m, others, out)
        except (ArgParseFinished, ArgParseError):
            return ArgumentParserResult(None)

        return self._execute(m, out, handler, parsed, others, output_format)

    def _get_args_itr(self, args):
        all_global_args = set(
            a.lstrip('-/') for a in self.help_args | self.complete_args | self.global_args)
        def not_global(a):
            return a.lstrip('-/') not in all_global_args
        it = filter(not_global, args).__iter__() #pylint: disable=bad-builtin
        return it

    def _get_noun_map(self, args, it, out):
        m = self.noun_map
        n = next(it, '')
        while n:
            try:
                m = m[n.lower()]
            except LookupError:
                if '$args' not in m:
                    print(L('\nCommand "{0}" not found, names starting with "{0}":\n'.format(n)),
                          file=out)
                    self._display_completions(m, args, out=out)
                    raise ArgParseFinished()
                break
            n = next(it, '')
        return m, n

    def _parse_nouns(self, expected_kwargs, it, m, n, out): #pylint: disable=too-many-arguments
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
                        print(L("argument '{0}' does not take a value").format(key_n),
                              file=out)
                        self._display_usage(m)
                        raise ArgParseFinished()
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
        return others, parsed

    def _get_noun_data(self, m, n, args, out):
        try:
            expected_kwargs = m['$kwargs']
            handler = m['$handler']
        except LookupError:
            logger.debug('Missing data for noun %s', n)
            self._display_children(m, args, out=out)
            raise ArgParseFinished()
        return expected_kwargs, handler

    @staticmethod
    def _handle_required_args(expected_kwargs, parsed, out):
        required_args = [x for x, _, req, _ in expected_kwargs.values() if req]
        for a in required_args:
            try:
                parsed[a]
            except KeyError:
                msg = L("Missing required argument '{}'.".format(a))
                print(msg, file=out)
                raise ArgParseError(msg)

    def _get_output_format(self, m, others, out):
        try:
            output_format = others.pop('output') if others else None
            if output_format is not None and output_format not in OutputProducer.format_dict:
                print(L("Invalid output format '{}'.".format(output_format)), file=out)
                self._display_usage(m)
                raise ArgParseFinished()
        except KeyError:
            output_format = None
        return output_format

    def _execute(self, m, out, handler, parsed, others, output_format): #pylint: disable=too-many-arguments
        old_stdout = sys.stdout
        try:
            sys.stdout = out
            return ArgumentParserResult(handler(parsed, others), output_format)
        except IncorrectUsageError as ex:
            print(str(ex), file=out)
            return ArgumentParserResult(self._display_usage(m, out))
        finally:
            sys.stdout = old_stdout

    @staticmethod
    def _display_usage(noun_map, out=sys.stdout):
        subnouns = sorted(k for k in noun_map if not k.startswith('$'))
        argdoc = noun_map.get('$argdoc')
        delimiters = noun_map['$doc'][:-4]

        doc = GroupHelpFile(delimiters, subnouns) \
              if len(subnouns) > 0 \
              else CommandHelpFile(delimiters, argdoc)
        doc.load(noun_map)
        #doc.load_from_file()
        print_detailed_help(doc, out)

    def _display_completions(self, noun_map, arguments, out=sys.stdout):
        nouns = self._get_noun_matches(arguments, noun_map, out)
        last_arg = arguments[-1] if len(arguments) > 0 else ''
        matches = [k for k in nouns if k.startswith(last_arg)]
        print('\n'.join(sorted(set(matches))), file=out)
        out.flush()

    def _display_children(self, noun_map, arguments, out=sys.stdout):
        nouns = self._get_noun_matches(arguments, noun_map, out)
        print('\n'.join(sorted(set(nouns))), file=out)
        out.flush()

    def _get_noun_matches(self, arguments, noun_map, out):
        for a in self.complete_args:
            try:
                arguments.remove(a)
            except ValueError:
                pass

        kwargs = noun_map.get('$kwargs') or []
        last_arg = arguments[-1] if len(arguments) > 0 else ''
        args_candidates = []

        arguments_set = set(arguments)
        for a in kwargs:
            alias = kwargs[a][3]
            #check whether the arg has been used already
            if not [x for x in alias if x in arguments_set]:
                args_candidates.extend(alias)

        if last_arg.startswith('-') and (last_arg in args_candidates):
            print('\n', file=out) # TODO: parameter value completion is N.Y.I
            return []
        else:
            subcommand_candidates = [k for k in noun_map if not k.startswith('$')]
            candidates = subcommand_candidates + args_candidates
            return candidates

class ArgParseError(Exception):
    pass

class ArgParseFinished(Exception):
    pass
