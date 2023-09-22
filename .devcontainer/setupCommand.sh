#!/bin/bash
source ./env/bin/activate

azdev setup --cli .
az --version