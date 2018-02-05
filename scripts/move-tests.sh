#!/bin/bash

for test_folder in `find src/command_modules -name tests`; do
    p=`dirname $test_folder`
    t=$p/test_temp
    mv $test_folder $t

    if [ -d $t/recordings/2017-03-09-profile ]; then
        mkdir -p $test_folder/profile_2017_03_09
        cp -r $t/* $test_folder/profile_2017_03_09
        rm -r $test_folder/profile_2017_03_09/recordings
        mkdir -p $test_folder/profile_2017_03_09/recordings
        cp -r $t/recordings/2017-03-09-profile/* $test_folder/profile_2017_03_09/recordings/
    fi

    mkdir -p $test_folder/latest
    cp -r $t/* $test_folder/latest/
    
    if [ -d $t/recordings/latest ]; then
        rm -r $test_folder/latest/recordings
        mkdir -p $test_folder/latest/recordings
        cp -r $t/recordings/latest/* $test_folder/latest/recordings/
    fi

    rm -r $t

done
