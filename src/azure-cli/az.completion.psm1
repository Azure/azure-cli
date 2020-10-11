$AzCommand = "az"

$AzArgCompleteScriptBlock = {
    param($wordToComplete, $commandAst, $cursorPosition)

    # In case of scripts, this object hold the current line after string conversion
    $line = "$commandAst"

    # The behaviour of completion should depend on the trailing spaces in the current line:
    # * "command subcommand " --> TAB --> Completion items parameters/sub-subcommands of "subcommand"
    # * "command subcom" --> TAB --> Completion items to extend "subcom" into matching subcommands.
    # $line never contains the trailing spaces. However, $cursorPosition is the length of the original
    # line (with trailing spaces) in this case. This comparision allows the expected user experience.
    if ($cursorPosition -gt $line.Length) {
        $line = "$line "
    }

    # Mock bash with environment variable settings
    New-Item -Path Env: -Name _ARGCOMPLETE -Value 1 | Out-Null # Enables tab complition in argcomplete
    New-Item -Path Env: -Name COMP_TYPE -Value 9 | Out-Null # Constant
    New-Item -Path Env: -Name _ARGCOMPLETE_IFS -Value " " | Out-Null # Separator of the items
    New-Item -Path Env: -Name _ARGCOMPLETE_SUPPRESS_SPACE -Value 1 | Out-Null # Constant
    New-Item -Path Env: -Name _ARGCOMPLETE_COMP_WORDBREAKS -Value "" | Out-Null # Constant
    New-Item -Path Env: -Name COMP_POINT -Value $cursorPosition | Out-Null # Refers to the last character of the current line
    New-Item -Path Env: -Name COMP_LINE -Value $line | Out-Null # Current line

    # Set a special environment variable to mark that the completion is executed by PowerShell
    New-Item -Path Env: -Name _ARGCOMPLETE_POWERSHELL -Value 1 | Out-Null

    # Just call the script without any parameter
    # Since the environment variables are set, the argcomplete.autocomplete(...) function will be executed.
    # The result will be printed on the standard output (see the details in the Python file).
    try {
        Invoke-Expression $AzCommand -OutVariable completionResult -ErrorVariable errorOut -ErrorAction SilentlyContinue | Out-Null
    }
    catch {
        # Hide all errors
    }

    # Delete environment variables
    Remove-Item Env:\_ARGCOMPLETE | Out-Null
    Remove-Item Env:\COMP_TYPE | Out-Null
    Remove-Item Env:\_ARGCOMPLETE_IFS | Out-Null
    Remove-Item Env:\_ARGCOMPLETE_SUPPRESS_SPACE | Out-Null
    Remove-Item Env:\_ARGCOMPLETE_COMP_WORDBREAKS | Out-Null
    Remove-Item Env:\COMP_POINT | Out-Null
    Remove-Item Env:\COMP_LINE | Out-Null
    
    Remove-Item Env:\_ARGCOMPLETE_POWERSHELL | Out-Null
    
    # Splitting only works if there were any compiletion result
    if ($completionResult.Count -gt 0) {
        # If there is only one completion item, it will be immediately used. In this case
        # a trailing space is important to show the user that the complition for the current
        # item is ready.
        $items = "$completionResult".Split()
        if ($items -eq $completionResult) {
            "$items "
        }
        else {
            $items
        }
    }
}

# Register tab completion for the mat command
Register-ArgumentCompleter -Native -CommandName $AzCommand -ScriptBlock $AzArgCompleteScriptBlock
