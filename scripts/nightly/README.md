Nightly Builds
==============

The scripts in this directory are used for creating nightly builds.


Usage
-----

Environment variables that should be set:  
PYPI_REPO
PYPI_USER
PYPI_PASS

For example, add the following to the crontab:  

00 04 * * * sudo docker run -t -v /home/ubuntu/build:/nightly -e "TZ=America/Los_Angeles" -e "PYPI_REPO=http://0.0.0.0:8080" -e "PYPI_USER=pypiusername" -e "PYPI_PASS=mypassword" python:3.5 nightly/nightly-build.sh
