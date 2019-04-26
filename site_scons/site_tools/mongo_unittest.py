"""Pseudo-builders for building and registering unit tests."""
from SCons.Script import Action


def exists(env):
    return True


_unittests = []
def register_unit_test(env, test):
    _unittests.append(test.path)
    env.Alias('$UNITTEST_ALIAS', test)

def unit_test_list_builder_action(env, target, source):
    ofile = open(str(target[0]), 'w')
    try:
        for s in _unittests:
            print('\t' + str(s))
            ofile.write('%s\n' % s)
    finally:
        ofile.close()

def build_cpp_unit_test(env, target, source, **kwargs):
    libdeps = kwargs.get('LIBDEPS', [])
    libdeps.append( '$BUILD_DIR/mongo/unittest/unittest_main' )

    kwargs['LIBDEPS'] = libdeps
    kwargs['ADDITIONAL_COMPONENTS'] = {'tests', 'unittests'}
    if (
            "COMPONENT_TAG" in kwargs
            and not kwargs["COMPONENT_TAG"].endswith("-test")
    ):
        kwargs["COMPONENT_TAG"] += "-test"

    if "ROLE_TAG" not in kwargs:
        kwargs["ROLE_TAG"] = "runtime"

    result = env.Program(target, source, **kwargs)
    env.RegisterUnitTest(result[0])
    hygienic = env.GetOption('install-mode') == 'hygienic'
    if not hygienic:
        env.Install("#/build/unittests/", result[0])
    return result


def generate(env):
    env.Command('$UNITTEST_LIST', env.Value(_unittests),
                Action(unit_test_list_builder_action, "Generating $TARGET"))
    env.AddMethod(register_unit_test, 'RegisterUnitTest')
    env.AddMethod(build_cpp_unit_test, 'CppUnitTest')
    env.Alias('$UNITTEST_ALIAS', '$UNITTEST_LIST')
