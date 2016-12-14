require 'tmpdir'

class AzureCli2 < Formula
  include Language::Python::Virtualenv

  desc "Azure CLI 2.0"
  homepage "https://github.com/Azure/azure-cli"
  # NOTE: When releasing, this should point to a version that is not '+dev'
  url "https://github.com/Azure/azure-cli/archive/all-v0.1.0b11.tar.gz"
  version "0.1.0b11"
  depends_on "python"
  sha256 "da6d4d523acbb05133b11ffe0c601c020c7da151ee0d68bc7d045783476f38d0"

  bottle do
    cellar :any_skip_relocation
    sha256 "e34b9409ae68dae52b20cc196e3fb90450c525f3017e7294cd4e31cbdb57510d" => :sierra
  end

  # Apply the 'az component' patch for src/command_modules/azure-cli-component/azure/cli/command_modules/component/custom.py
  # Create a new patch by doing the following:
  #     1. Modify the custom.py file (see example in homebrew/patch_component_custom.py).
  #     2. Run git diff to get the patch: $ git diff src/command_modules/azure-cli-component/azure/cli/command_modules/component/custom.py
  #     3. Publish the patch publicly and include the link here.
  patch do
    url "https://gist.githubusercontent.com/derekbekoe/b753179bff1b25343cbf38fc90c8c170/raw/e72ae0b0741fa10269fcde6e46c91122acbd5090/azure_cli_patch_component_010b11_custom.diff"
    sha256 "7657927127349eda7ae0d8116739d397b115624151cf05d3ed4df017b34d1c72"
  end

  def completion_script; <<-EOS.undent
    _python_argcomplete() {
        local IFS='\v'
        COMPREPLY=( $(IFS="$IFS"                   COMP_LINE="$COMP_LINE"                   COMP_POINT="$COMP_POINT"                   _ARGCOMPLETE_COMP_WORDBREAKS="$COMP_WORDBREAKS"                   _ARGCOMPLETE=1                   "$1" 8>&1 9>&2 1>/dev/null 2>/dev/null) )
        if [[ $? != 0 ]]; then
            unset COMPREPLY
        fi
    }
    complete -o nospace -F _python_argcomplete "az"
    EOS
  end

  def install
    venv = virtualenv_create(libexec)
    Dir.mktmpdir {|tmp_dir|
        pkg_dirs = ['src/azure-cli', 'src/azure-cli-core', 'src/azure-cli-nspkg']
        pkg_dirs += Dir.glob('src/command_modules/azure-cli-*/')
        # Build the packages
        pkg_dirs.each do |item|
            Dir.chdir(item){
              system libexec/"bin/python", "setup.py", "bdist_wheel", "-d", tmp_dir
            }
        end
        # Install the CLI and all optional modules
        cmd_mods = Dir.entries('src/command_modules/').select {|f| !(f =='.' || f == '..')}
        system libexec/"bin/pip", "install", "azure-cli", *cmd_mods, "-f", tmp_dir
    }
    # Write the executable
    bin_dir = libexec/"bin"
    File.write("#{bin_dir}/az", "#!/usr/bin/env bash\n#{bin_dir}/python -m azure.cli \"$@\"")
    bin.install_symlink "#{libexec}/bin/az"
    # Bash tab completion
    File.write(libexec/"az.completion", completion_script)
    bash_completion.install libexec/"az.completion"
  end

  def caveats; <<-EOS.undent
    To complete tab completion set up:
      1. Modify your ~/.bash_profile (if the line doesn't already exist)
        $ echo "[ -f #{HOMEBREW_PREFIX}/etc/bash_completion.d/az.completion ] && . #{HOMEBREW_PREFIX}/etc/bash_completion.d/az.completion" >> ~/.bash_profile
      2. Restart your shell
        $ exec -l $SHELL
    ----
    Get started with:
      $ az configure
    EOS
  end

  test do
    bin_dir = libexec/"bin"
    system bin_dir/"az", "--version"
    assert_match "complete -o nospace -F _python_argcomplete az",
      shell_output("bash -c 'source #{bash_completion}/az.completion && complete -p az'")
  end

end
