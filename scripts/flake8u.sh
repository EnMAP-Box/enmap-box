#!/bin/bash
# runs flake8 for uncommitted files only.
#
flake8 $(git status -s | grep -E '\.py$' | cut -c 4-)
