#!/bin/bash

green="\033[0;32"
nc="\033[0m" # No Color

is_thing_up() {
    thing=$1

    result=$(ps aux | grep ${thing} | head -n -1 | awk -F " " '{print $(NF-1), $NF}')

    printf "%-15s %s \n" "${thing}" "${result}"

}


for thing in "simple-writer" "producer" "commander.py"; do
    is_thing_up ${thing}
done
	     
