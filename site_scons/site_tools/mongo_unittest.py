# Copyright 2019 MongoDB Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''Pseudo-builders for building and registering unit tests.'''
from SCons.Script import Action


def exists(env):
    return True


_unittests = []
def register_unit_test(env, test):
    _unittests.append(test.path)
    env.GenerateTestExecutionAliases(test)
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
    unit_test_components = {'tests', 'unittests'}
    if (
            'AIB_COMPONENT' in kwargs
            and not kwargs['AIB_COMPONENT'].endswith('-test')
    ):
        kwargs['AIB_COMPONENT'] += '-test'

    if 'AIB_COMPONENTS_EXTRA' in kwargs:
        kwargs['AIB_COMPONENTS_EXTRA'] = set(kwargs['AIB_COMPONENTS_EXTRA']).union(unit_test_components)
    else:
        kwargs['AIB_COMPONENTS_EXTRA'] = unit_test_components

    result = env.Program(target, source, **kwargs)
    env.RegisterUnitTest(result[0])

    return result


def generate(env):
    env.Command('$UNITTEST_LIST', env.Value(_unittests),
                Action(unit_test_list_builder_action, 'Generating $TARGET'))
    env.AddMethod(register_unit_test, 'RegisterUnitTest')
    env.AddMethod(build_cpp_unit_test, 'CppUnitTest')
    env.Alias('$UNITTEST_ALIAS', '$UNITTEST_LIST')
