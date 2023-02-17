#!/bin/bash

if grep -E '^##\s*[^ ]*\s*Breaking Changes$' tmp-changelog.md &> /dev/null; then
    echo "MINOR"
elif grep -E '^##\s*[^ ]*\s*Features$' tmp-changelog.md &> /dev/null; then
    echo "MINOR"
elif grep -E '^##\s*[^ ]*\s*Fixes$' tmp-changelog.md &> /dev/null; then
    echo "PATCH"
else
    echo "##### Can not detect any version increment! #####"
    exit 1
fi