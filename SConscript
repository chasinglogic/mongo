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
