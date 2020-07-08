import os
import sys
import subprocess

d = '/usr/lib64/az/lib/python3.6/site-packages/azure/cli/command_modules'
mod_list = [os.path.join(d, o) for o in os.listdir(d) if os.path.isdir(os.path.join(d, o))]
# mod_list= ['/usr/lib64/az/lib/python3.6/site-packages/azure/cli/command_modules/botservice']

for mod in mod_list:
    mod_name = os.path.basename(os.path.normpath(mod))
    if mod_name == 'botservice':
        subprocess.call(['export PYTHONPATH=/usr/lib64/az/lib/python3.6/site-packages && python3 -m pytest -x -v --boxed -p no:warnings --log-level=WARN --junit-xml /result/{}.xml {}'.format(mod_name, mod)], shell=True)
    subprocess.call(['export PYTHONPATH=/usr/lib64/az/lib/python3.6/site-packages && python3 -m pytest -x -v --boxed -p no:warnings --log-level=WARN --junit-xml /result/{}.xml -n auto {}'.format(mod_name, mod)], shell=True)


