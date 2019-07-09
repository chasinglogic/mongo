#!/bin/bash

set -o verbose
set -o errexit

# This script downloads and import yaml-cpp
# Yaml-cpp does not use any autotools/cmake/config system to it is a simple import.
# This script is designed to run on Linux or Mac OS X
#
# Yaml-cpp tarballs use the name "yaml-cpp-yaml-cpp-$VERSION" so we need to rename it
#

VERSION=0.6.2
NAME=yaml-cpp
TARBALL=$NAME-$VERSION.tar.gz
TARBALL_DESTDIR=$NAME-$NAME-$VERSION
DESTDIR=`git rev-parse --show-toplevel`/src/third_party/$NAME-$VERSION

if [ ! -f $TARBALL ]; then
    echo "Get tarball"
    wget https://github.com/jbeder/yaml-cpp/archive/$TARBALL
fi

tar -zxvf $TARBALL

rm -rf $DESTDIR

mv $TARBALL_DESTDIR $DESTDIR

# Prune sources
echo "Prune tree"
rm -rf $DESTDIR/test
rm -rf $DESTDIR/util
rm -f $DESTDIR/CMakeLists.txt
rm -f $DESTDIR/*.cmake*

# Note: There are no config.h or other build artifacts to generate
echo "Done"
