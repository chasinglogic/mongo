#!/bin/bash
# Script to set up JSON Schema Test Suite

set -euo pipefail
IFS=$'\n\t'

if [ "$#" -ne 0 ]; then
	echo "This script does not take any arguments"
	exit 1
fi

TEMP_DIR=$(mktemp -d /tmp/json_schema.XXXXXX)
trap "rm -rf $TEMP_DIR" EXIT
DESTDIR=$(git rev-parse --show-toplevel)/src/third_party/JSON-Schema-Test-Suite

rm -rf $TEMP_DIR/*

git clone https://github.com/json-schema-org/JSON-Schema-Test-Suite.git $TEMP_DIR

# Use a specific commit
git -C $TEMP_DIR checkout 728066f9c5c258ba3b1804a22a5b998f2ec77ec0

rm -rf $DESTDIR
mkdir -p $DESTDIR/tests/draft4

cp $TEMP_DIR/LICENSE $DESTDIR
cp $TEMP_DIR/README.md $DESTDIR
cp -r $TEMP_DIR/tests/draft4 $DESTDIR/tests/
