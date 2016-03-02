if type compdef &>/dev/null; then
  #ZSH
  _az_complete() {
    compadd -- `"${COMP_WORDS[0]}" --complete "${words[@]:1}"`
  }
  compdef _az_complete az
elif type complete &>/dev/null; then
  #BASH
  _az_complete() {
    COMPREPLY=( $(compgen -W '$("${COMP_WORDS[0]}" --complete "${COMP_WORDS[@]:1}")' -- "${COMP_WORDS[COMP_CWORD]}") )
  }
  complete -F _az_complete az
fi
