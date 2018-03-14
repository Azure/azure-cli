#How to generate the Sphinx help file output#

## Set up environment ##

1. Inside a Python virtual environment, run "pip install sphinx==1.6.7"
2. If Az isn't set up in this virtual environment, run "python scripts\dev_setup.py" from azure-cli

## Run Sphinx ##

1. From azure-cli\doc\sphinx, run "make xml" 

## Retrieve output ##

1. XML output is stored in azure-cli\doc\sphinx\_build\xml\ind.xml 