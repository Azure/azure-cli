case $SHELL in
*/zsh)
   echo 'Enabling ZSH compatibility mode';
   autoload bashcompinit && bashcompinit
   ;;
*/bash)
   ;;
*)
esac

eval "$(register-python-argcomplete az)"
