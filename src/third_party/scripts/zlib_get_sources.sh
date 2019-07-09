#!/usr/bin/env bash

set -o verbose
set -o errexit

# This script downloads and import zlib
# Zlib does not need to use any autotools/cmake/config system to it is a simple import.
# This script is designed to run on most unix-like OSes
#

VERSION=1.2.11
NAME=zlib
TARBALL=${NAME}-${VERSION}.tar.gz
TARBALL_DESTDIR=${NAME}-${VERSION}
DESTDIR=$(git rev-parse --show-toplevel)/src/third_party/${NAME}-${VERSION}

echo ${DESTDIR}

rm -fr ${TARBALL_DESTDIR}
rm -f ${TARBALL}

if [ ! -f ${TARBALL} ]; then
    echo "Get tarball"
    wget https://www.zlib.net/${TARBALL}
fi

tar -zxvf ${TARBALL}

rm -rf ${DESTDIR}
mkdir ${DESTDIR}

# Just move the sources
mv ${TARBALL_DESTDIR}/*.{h,c} ${DESTDIR}

# Move the readme and such.
mv ${TARBALL_DESTDIR}/{README,FAQ,INDEX} ${DESTDIR}

rm -fR ${TARBALL_DESTDIR}


# Generate the SConscript
( cat > ${DESTDIR}/SConscript ) << ___EOF___
# -*- mode: python; -*-
Import("env")

env = env.Clone()

env.Append(CPPDEFINES=["HAVE_STDARG_H"])
if not env.TargetOSIs('windows'):
    env.Append(CPPDEFINES=["HAVE_UNISTD_H"])

env.Library(
    target="zlib",
    source=[
        'adler32.c',
        'crc32.c',
        'compress.c',
        'deflate.c',
        'infback.c',
        'inffast.c',
        'inflate.c',
        'inftrees.c',
        'trees.c',
        'uncompr.c',
        'zutil.c',
    ],
    LIBDEPS_TAGS=[
        'init-no-global-side-effects',
    ],
)
___EOF___

rm -f ${TARBALL}


# Note: There are no config.h or other build artifacts to generate
echo "Done"
