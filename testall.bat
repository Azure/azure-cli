@echo off
cd src
python -m unittest discover -s azure\cli\tests
cd..
