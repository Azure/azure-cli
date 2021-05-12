import subprocess
import re

def fix_strings(text: str):
    return text.replace("*", "").replace("'","").replace('"',"")


with open("az.fish", "w") as f:
    subcommands = [['az']]

    command_lines_re = re.compile('^\s{4}(?!az)\w+(\w|-)+.*')
    flag_lines_re = re.compile('^\s{4}--(\w|-)+.*')
    command_re = re.compile('\w+(\w|-)+(?=\s+:)')
    flag_re = re.compile('--(\w|-)+(?=\s+:)')
    description_re = re.compile('(?<=:\s).*$')

    output = []
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

        command = subcommands.pop()
        response = subprocess.run( command + ['--help'], stdout=subprocess.PIPE).stdout.decode('utf-8')

        lines = response.split('\n')


        condition = ""
        root_cmds = []

        if is_az:
            condition = '-n "__fish_az_no_subcommand"'
        else:
            condition = '-A -n "__is_az_subcommand \'' + " ".join(command[1:]) + '\'"'

        for line in lines:
            command_match = command_lines_re.match(line)
            flag_match = flag_lines_re.match(line)

            if command_match != None:
                sub_cmd = command_re.search(line)
                desc    = description_re.search(line)

                if sub_cmd != None and desc != None:
                    matched_sub_cmd = sub_cmd.group()
                    if is_az:
                        root_cmds.append(matched_sub_cmd)
                    subcommands.append(command + [matched_sub_cmd])
                    desc_text = fix_strings(desc.group())
                    f.write(f'complete -c az -d "{desc_text}" {condition} -f -a "{matched_sub_cmd}"\n')
            if flag_match != None:
                flag    = flag_re.search(line)
                desc    = description_re.search(line)

                if flag != None and desc != None:
                    matched_flag = flag.group()
                    matched_flag = matched_flag[2:]
                    desc_text = fix_strings(desc.group())
                    f.write(f'complete -c az -d "{desc_text}" {condition} -f -l "{matched_flag}"\n')

        if is_az:
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

        is_az = False
