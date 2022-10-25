#!/usr/bin/env bash

echo "html_description=$(echo $INPUT_JSON_DESCRIPTION | python /format-change-set-json-as-html.py)" >> $GITHUB_OUTPUT