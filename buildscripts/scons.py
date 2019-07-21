#!/usr/bin/env python3
"""Scons module."""

import os
import sys

SCONS_VERSION = os.environ.get('SCONS_VERSION', "3.1.0")

MONGODB_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
SCONS_DIR = os.path.join(MONGODB_ROOT, 'src', 'third_party', 'scons-' + SCONS_VERSION,
                         'scons-local-' + SCONS_VERSION)

if not os.path.exists(SCONS_DIR):
    print("Could not find SCons in '%s'" % (SCONS_DIR))
    sys.exit(1)

sys.path = [SCONS_DIR] + sys.path

try:
    import SCons.Script
except ImportError:
    print("Could not find SCons in '%s'" % (SCONS_DIR))
    sys.exit(1)

SCons.Script.main()
