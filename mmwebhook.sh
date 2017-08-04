#!/usr/bin/bash

header="Content-Type: application/json"
request_body=$(cat <<EOF
{
  "username": "CheckMK",
  "text": "@all\n$1"
}
EOF
)

curl -i -X POST -H "$header" -d "$request_body" https://mm.cocus.com/hooks/cpaync5z73ro3yuuifcbmi16do
