Import("env")

env = env.Clone()

env.SConscript(
    dirs=[
        'src',
        'jstests',
    ],
    duplicate=False,
    exports=[
        'env',
    ],
)
