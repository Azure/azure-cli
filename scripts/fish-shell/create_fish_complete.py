import subprocess
import re

# Sanatize input
def fix_strings(text: str):
    return text.replace("*", "").replace("'","").replace('"',"")

# Write to local az.fish
with open("az.fish", "w") as f:
    subcommands = [['az']]

    # Match on lines that we care about (lines that are tabbed and :)
    command_lines_re = re.compile('^\s{4}(?!az)\w+(\w|-)+.*')
    # Match linescontaing a flag
    flag_lines_re = re.compile('^\s{4}--(\w|-)+.*')
    # Parse out commands (eg az --help will parse out account, acr, etc)
    command_re = re.compile('\w+(\w|-)+(?=\s+:)')
    # Parse out command flags (eg --help)
    flag_re = re.compile('--(\w|-)+(?=\s+:)')
    # Parse out descriptions (anything after :)
    description_re = re.compile('(?<=:\s).*$')

    output = []

    # Create a function to match on a specific command
    f.write('''
function __is_az_subcommand
    set -l cmd (commandline -poc)
    set args (string join ' ' $argv)
    set sub (string join ' ' $cmd[2..])
    if [ "$sub" = "$args" ]
        return 0
    end
    return 1
end
''')

    is_az = True

    while len(subcommands) != 0:

        # Grab last item in queue (DFS)
        command = subcommands.pop()
        # Query back help page
        response = subprocess.run( command + ['--help'], stdout=subprocess.PIPE).stdout.decode('utf-8')

        lines = response.split('\n')


        condition = ""
        root_cmds = []

        # if its a root command
        if is_az:
            condition = '-n "__fish_az_no_subcommand"'
        else:
            condition = '-A -n "__is_az_subcommand \'' + " ".join(command[1:]) + '\'"'

        for line in lines:
            command_match = command_lines_re.match(line)
            flag_match = flag_lines_re.match(line)

            # this contains a subcommand, parse out command and description
            if command_match != None:
                sub_cmd = command_re.search(line)
                desc    = description_re.search(line)

                if sub_cmd != None and desc != None:
                    matched_sub_cmd = sub_cmd.group()
                    if is_az:
                        root_cmds.append(matched_sub_cmd)
                    # Add new found command to parsing queue
                    subcommands.append(command + [matched_sub_cmd])
                    desc_text = fix_strings(desc.group())
                    # Write complete command to file
                    f.write(f'complete -c az -d "{desc_text}" {condition} -f -a "{matched_sub_cmd}"\n')

            # This contains a flag
            if flag_match != None:
                flag    = flag_re.search(line)
                desc    = description_re.search(line)

                if flag != None and desc != None:
                    matched_flag = flag.group()
                    matched_flag = matched_flag[2:]
                    desc_text = fix_strings(desc.group())
                    # Write complete with long flag option
                    f.write(f'complete -c az -d "{desc_text}" {condition} -f -l "{matched_flag}"\n')

        if is_az:
            # Function to test if root command
            f.write('''
function __fish_az_no_subcommand
    for i in (commandline -opc)
        if contains -- $i ''')
            f.write(" ".join(root_cmds))
            f.write('''
            return 1
        end
    end
    return 0
end
''')

        # toggle off after parsing root commands
        is_az = False
