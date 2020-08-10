#!/usr/bin/env python

try:
    from shlex import quote
except ImportError:
    from pipes import quote

bashcode = r'''
# Run something, muting output or redirecting it to the debug stream
# depending on the value of _ARC_DEBUG.
__python_argcomplete_run() {
    if [[ -z "$_ARC_DEBUG" ]]; then
        "$@" 8>&1 9>&2 1>/dev/null 2>&1
    else
        "$@" 8>&1 9>&2 1>&9 2>&1
    fi
}

_python_argcomplete() {
    local IFS=$'\013'
    local SUPPRESS_SPACE=0
    if compopt +o nospace 2> /dev/null; then
        SUPPRESS_SPACE=1
    fi
    COMPREPLY=( $(IFS="$IFS" \
                  COMP_LINE="$COMP_LINE" \
                  COMP_POINT="$COMP_POINT" \
                  COMP_TYPE="$COMP_TYPE" \
                  _ARGCOMPLETE_COMP_WORDBREAKS="$COMP_WORDBREAKS" \
                  _ARGCOMPLETE=1 \
                  _ARGCOMPLETE_SUPPRESS_SPACE=$SUPPRESS_SPACE \
                  __python_argcomplete_run "$1") )
    if [[ $? != 0 ]]; then
        unset COMPREPLY
    elif [[ $SUPPRESS_SPACE == 1 ]] && [[ "$COMPREPLY" =~ [=/:]$ ]]; then
        compopt -o nospace
    fi
}
complete %(complete_opts)s -F _python_argcomplete %(executables)s
'''

tcshcode = '''\
complete "%(executable)s" 'p@*@`python-argcomplete-tcsh "%(executable)s"`@' ;
'''

fishcode = r'''
function __fish_%(executable)s_complete
    set -x _ARGCOMPLETE 1
    set -x _ARGCOMPLETE_IFS \n
    set -x _ARGCOMPLETE_SUPPRESS_SPACE 1
    set -x _ARGCOMPLETE_SHELL fish
    set -x COMP_LINE (commandline -p)
    set -x COMP_POINT (string length (commandline -cp))
    set -x COMP_TYPE
    if set -q _ARC_DEBUG
        %(executable)s 8>&1 9>&2 1>/dev/null 2>&1
    else
        %(executable)s 8>&1 9>&2 1>&9 2>&1
    end
end
complete -c %(executable)s -f -a '(__fish_%(executable)s_complete)'
'''


def shellcode(executables, use_defaults=True, shell='bash', complete_arguments=None):
    '''
    Provide the shell code required to register a python executable for use with the argcomplete module.

    :param str executables: Executables to be completed (when invoked exactly with this name
    :param bool use_defaults: Whether to fallback to readline's default completion when no matches are generated.
    :param str shell: Name of the shell to output code for (bash or tcsh)
    :param complete_arguments: Arguments to call complete with
    :type complete_arguments: list(str) or None
    '''

    if complete_arguments is None:
        complete_options = '-o nospace -o default -o bashdefault' if use_defaults else '-o nospace -o bashdefault'
    else:
        complete_options = " ".join(complete_arguments)

    if shell == 'bash':
        quoted_executables = [quote(i) for i in executables]
        executables_list = " ".join(quoted_executables)
        code = bashcode % dict(complete_opts=complete_options, executables=executables_list)
    elif shell == 'fish':
        code = ""
        for executable in executables:
            code += fishcode % dict(executable=executable)
    else:
        code = ""
        for executable in executables:
            code += tcshcode % dict(executable=executable)

    return code
