#!/bin/bash
#--data-binary $file_reference \
host="$1"
name="rgbcct"
curl \
    --request GET \
    http://$host:8008/$name
