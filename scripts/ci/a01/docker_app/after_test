#!/bin/bash

mount_path=$1
task=$2

recording_path=$(echo $task | jq -r ".settings.execution.recording")
if [ "$recording_path" == "null" ]; then
    echo "Skip copying recording file. Code 1."
    exit 0
fi

if [ -z "$recording_path" ]; then
    echo "Skip copying recording file. Code 2."
    exit 0
fi

run_id=$(echo $task | jq -r ".run_id")
task_id=$(echo $task | jq -r ".id")

mkdir -p $mount_path/$run_id
cp $recording_path $mount_path/$run_id/recording_$task_id.yaml
