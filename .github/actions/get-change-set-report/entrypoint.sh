#!/usr/bin/env bash

echo ::set-output name=html_description::$(echo $INPUT_JSON_DESCRIPTION | python format-change-set-json-as-html.py)