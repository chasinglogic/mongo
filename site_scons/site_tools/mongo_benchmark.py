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

"""
Pseudo-builders for building and registering benchmarks.
"""
from SCons.Script import Action

def exists(env):
    return True

_benchmarks = []
def register_benchmark(env, test):
    _benchmarks.append(test.path)
    env.GenerateTestExecutionAliases(test)
    env.Alias('$BENCHMARK_ALIAS', test)


def benchmark_list_builder_action(env, target, source):
    ofile = open(str(target[0]), 'w')
    try:
        for s in _benchmarks:
            print('\t' + str(s))
            ofile.write('%s\n' % s)
    finally:
        ofile.close()

def build_benchmark(env, target, source, **kwargs):

    bmEnv = env.Clone()
    bmEnv.InjectThirdParty(libraries=['benchmark'])

    if bmEnv.TargetOSIs('windows'):
        bmEnv.Append(LIBS=["ShLwApi.lib"])

    libdeps = kwargs.get('LIBDEPS', [])
    libdeps.append('$BUILD_DIR/mongo/unittest/benchmark_main')

    kwargs['LIBDEPS'] = libdeps
    kwargs['INSTALL_ALIAS'] = ['benchmarks']

    benchmark_test_components = {'tests', 'benchmarks'}
    if (
            'AIB_COMPONENT' in kwargs
            and not kwargs['AIB_COMPONENT'].endswith('-benchmark')
    ):
        kwargs['AIB_COMPONENT'] += '-benchmark'

    if 'AIB_COMPONENTS_EXTRA' in kwargs:
        benchmark_test_components = set(kwargs['AIB_COMPONENTS_EXTRA']).union(benchmark_test_components)

    kwargs['AIB_COMPONENTS_EXTRA'] = benchmark_test_components

    result = bmEnv.Program(target, source, **kwargs)
    bmEnv.RegisterBenchmark(result[0])
    return result


def generate(env):
    env.Command('$BENCHMARK_LIST', env.Value(_benchmarks),
                Action(benchmark_list_builder_action, "Generating $TARGET"))
    env.AddMethod(register_benchmark, 'RegisterBenchmark')
    env.AddMethod(build_benchmark, 'Benchmark')
    env.Alias('$BENCHMARK_ALIAS', '$BENCHMARK_LIST')
