#!/bin/bash

green="\033[0;32"
nc="\033[0m" # No Color

is_thing_up() {
    thing=$1

    result=$(ps aux | grep ${thing} | grep -v grep | awk -F " " '{print $(NF-1), $NF}' | wc -l)

    printf "%-15s %s \n" "${thing}" "${result}"

}


for thing in "run-simple-writer" "run-producer" "commander.py"; do
    is_thing_up ${thing}
done
	     
