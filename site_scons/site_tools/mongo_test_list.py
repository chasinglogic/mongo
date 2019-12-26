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
"""Pseudo-builders for building test lists for Resmoke"""

import SCons
from collections import defaultdict

TEST_REGISTRY = defaultdict(list)


def register_test(env, file_name, test):
    if SCons.Util.is_String(file_name) and "$" in file_name:
        file_name = env.subst(file_name)
    elif getattr(test.attributes, "AIB_INSTALL_ACTIONS", []):
        file_name = getattr(test.attributes, "AIB_INSTALL_ACTIONS")[0].path
    else:
        file_name = file_name.path

    TEST_REGISTRY[file_name].append(test.path)
    env.GenerateTestExecutionAliases(test)


def test_list_builder_action(env, target, source):
    if SCons.Util.is_String(target[0]):
        filename = env.subst(target[0])
    else:
        filename = target[0].abspath

    source = [
        env.subst(s) if SCons.Util.is_String(s) else s.abspath
        for s in source
    ]

    with open(filename, "w") as ofile:
        tests = TEST_REGISTRY[filename]
        tests.extend(source)
        for s in tests:
            print("\t" + str(s))
            ofile.write("{}\n".format(str(s)))


TEST_LIST_BUILDER = SCons.Builder.Builder(
    action=SCons.Action.FunctionAction(
        test_list_builder_action,
        {"cmdstr": "Generating $TARGETS"},
    )
)


def exists(env):
    return True


def generate(env):
    env.Append(BUILDERS={"TestList": TEST_LIST_BUILDER})
    env.AddMethod(register_test, "RegisterTest")
