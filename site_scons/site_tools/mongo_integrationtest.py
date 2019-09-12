'''Pseudo-builders for building and registering integration tests.
'''
from SCons.Script import Action

def exists(env):
    return True

_integration_tests = []
def register_integration_test(env, test):
    installed_test = env.Install('#/build/integration_tests/', test)
    _integration_tests.append(installed_test[0].path)
    env.Alias('$INTEGRATION_TEST_ALIAS', installed_test)

def integration_test_list_builder_action(env, target, source):
    ofile = open(str(target[0]), 'w')
    try:
        for s in _integration_tests:
            print('\t' + str(s))
            ofile.write('%s\n' % s)
    finally:
        ofile.close()

def build_cpp_integration_test(env, target, source, **kwargs):
    libdeps = kwargs.get('LIBDEPS', [])
    libdeps.append( '$BUILD_DIR/mongo/unittest/integration_test_main' )

    kwargs['LIBDEPS'] = libdeps
    integration_test_components = {'tests', 'integration-tests'}

    if (
            'AIB_COMPONENT' in kwargs
            and not kwargs['AIB_COMPONENT'].endswith('-test')
    ):
        kwargs['AIB_COMPONENT'] += '-test'

    if 'AIB_COMPONENTS_EXTRA' in kwargs:
        kwargs['AIB_COMPONENTS_EXTRA'] = set(kwargs['AIB_COMPONENTS_EXTRA']).union(integration_test_components)
    else:
        kwargs['AIB_COMPONENTS_EXTRA'] = integration_test_components

    result = env.Program(target, source, **kwargs)
    env.RegisterIntegrationTest(result[0])
    return result


def generate(env):
    test_list = env.Command('$INTEGRATION_TEST_LIST', env.Value(_integration_tests),
                            Action(integration_test_list_builder_action, 'Generating $TARGET'))

    if env.GetOption("install-mode") == "hygienic":
        env.AutoInstall(
            target="$PREFIX_CONFDIR/resmokeconfig",
            source=test_list,
            AIB_COMPONENT="unittests",
            AIB_COMPONENTS_EXTRA=["tests"],
            AIB_ROLE="runtime",
        )
    
    env.AddMethod(register_integration_test, 'RegisterIntegrationTest')
    env.AddMethod(build_cpp_integration_test, 'CppIntegrationTest')
    env.Alias('$INTEGRATION_TEST_ALIAS', '$INTEGRATION_TEST_LIST')
