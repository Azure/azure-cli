Nightly Builds
==============

The scripts in this directory are used for creating nightly builds.

This README provides instructions on this build script, not how to install nightly builds.

Usage
-----

Copy nightly-build.sh and nightly-build.py from GitHub repo into /home/ubuntu/build directory.

chmod +x nightly-build.sh to make the script executable.

Environment variables that should be set:  
TZ
AZURE_STORAGE_CONNECTION_STRING

For example, add the following to the crontab:  

00 04 * * * sudo docker run -t -v /home/ubuntu/build:/nightly -e "TZ=America/Los_Angeles" -e "AZURE_STORAGE_CONNECTION_STRING=connection_string" python:3.5 nightly/nightly-build.sh
