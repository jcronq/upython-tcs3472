#!/bin/bash
#--data-binary $file_reference \
host="$1"
name="reboot"
curl \
    --request POST \
    http://$host:8008/$name
