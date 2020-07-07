import os 
import sys
import subprocess 

d = 'C:\\Program Files (x86)\\Microsoft SDKs\\Azure\\CLI2\\Lib\\site-packages\\azure\\cli\\command_modules'

mod_list = [os.path.join(d, o) for o in os.listdir(d) if os.path.isdir(os.path.join(d, o))]
for mod in mod_list:
    mod_name = os.path.basename(os.path.normpath(mod))
    
    # command = "python -m pytest -x -v -p no:warnings --log-level WARN --junit-xml '{}\\azure_cli_tests\\{}.xml' -n auto '{}'".format(os.path.expanduser('~'), mod_name, mod)
    subprocess.call(['python', '-m', 'pytest', '-x', '-v', '-p', 'no:warnings', '--log-level', 'WARN', 
        '--junit-xml', '{}\\azure_cli_tests\\{}.xml'.format(os.path.expanduser('~'), mod_name), '-n', 'auto', mod])
