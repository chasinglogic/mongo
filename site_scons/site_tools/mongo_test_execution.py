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

import os


def generate_test_execution_aliases(env, test):
    hygienic = env.GetOption('install-mode') == 'hygienic'
    if hygienic and getattr(test.attributes, "AIB_INSTALL_ACTIONS", []):
        installed = getattr(test.attributes, "AIB_INSTALL_ACTIONS")
    else:
        installed = [test]

    command = env.Command(
        target="#+{}".format(os.path.basename(installed[0].get_path())),
        source=installed,
        action="${SOURCES[0]}",
        NINJA_POOL="console",
    )

    env.Alias('test-execution-aliases', command)
    for source in test.sources:
        source_name = os.path.basename(source.get_path())
        # Strip suffix
        source_name = source_name[:source_name.rfind(".")]
        env.Alias(
            "test-execution-aliases",
            env.Alias(
                "+{}".format(source_name),
                command,
            )
        )


def exists(env):
    return True


def generate(env):
     # Wire up dependency for Ninja generator to collect the test
    # execution aliases
    test_execution_aliases = env.Alias('test-execution-aliases')
    env.Alias('all', test_execution_aliases)
    env.Alias('install-all-meta', test_execution_aliases)
    env.AddMethod(generate_test_execution_aliases, "GenerateTestExecutionAliases")
     # TODO: Remove when the new ninja generator is the only supported generator
    env['_NINJA_NO_TEST_EXECUTION'] = True
