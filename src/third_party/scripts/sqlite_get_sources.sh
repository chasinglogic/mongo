#!/bin/bash
# This script downloads and patches sqlite
#
# Turn on strict error checking, like perl use 'strict'
set -xeuo pipefail
IFS=$'\n\t'

if [ "$#" -ne 0 ]; then
    echo "This script does not take any arguments"
    exit 1
fi

IS_WSL=$(grep -q Microsoft /proc/version)

VERSION=3260000
RELEASEYEAR=2018
NAME=sqlite
PNAME=$NAME-amalgamation-$VERSION

GIT_EXE=git
if $IS_WSL; then
    GIT_EXE=git.exe
fi

if $IS_WSL; then
    TEMPDIR=$(wslpath -u $(powershell.exe -Command "Get-ChildItem Env:TEMP | Get-Content | Write-Host"))
else
    TEMPDIR="/tmp"
fi

SRC_ROOT=$(mktemp -d $TEMPDIR/$NAME.XXXXXX)

trap "rm -rf $SRC_ROOT" EXIT
SRC=${SRC_ROOT}/${PNAME}
DESTDIR=$($GIT_EXE rev-parse --show-toplevel)/src/third_party/$PNAME
PATCH_DIR=$($GIT_EXE rev-parse --show-toplevel)/src/third_party/$PNAME/patches
if $IS_WSL; then
    DESTDIR=$(wslpath -u "$DESTDIR")
    PATCH_DIR=$(wslpath -u "$PATCH_DIR")
fi

if [ ! -d $SRC ]; then

    pushd $SRC_ROOT

    wget https://sqlite.org/$RELEASEYEAR/$PNAME.zip
    unzip $PNAME.zip

    pushd $SRC

    patch < $PATCH_DIR/gethostuuid.patch

    popd
    popd
fi


test -d $DESTDIR/$NAME && rm -r $DESTDIR/$NAME
mkdir -p $DESTDIR/$NAME

mv $SRC/* $DESTDIR/$NAME/
