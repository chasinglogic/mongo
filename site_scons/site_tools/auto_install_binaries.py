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

# TODO: Versioned libraries
# TODO: library dependency chaining for windows dynamic builds, static dev packages
# TODO: Injectible component dependencies (jscore -> resmoke, etc.)
# TODO: Handle chmod state
# TODO: Installing resmoke and configurations
# TODO: package decomposition
# TODO: Install/package target help text
# TODO: implement sdk_headers

import os
import shlex
import itertools
from collections import defaultdict, namedtuple

import SCons
from SCons.Tool import install

ALIAS_MAP = "AIB_ALIAS_MAP"
SUFFIX_MAP = "AIB_SUFFIX_MAP"
PACKAGE_ALIAS_MAP = "AIB_PACKAGE_ALIAS_MAP"
PACKAGE_PREFIX = "AIB_PACKAGE_PREFIX"
ROLE_DEPENDENCIES = "AIB_ROLE_DEPENDENCIES"
COMPONENTS = "AIB_COMPONENTS_EXTRA"
INSTALL_ACTIONS = "AIB_INSTALL_ACTIONS"
ROLES = "AIB_ROLES"

PRIMARY_COMPONENT = "AIB_COMPONENT"
PRIMARY_ROLE = "AIB_ROLE"

AVAILABLE_ROLES = [
    "base",
    "debug",
    "dev",
    "meta",
    "runtime",
]

RoleInfo = namedtuple(
    'RoleInfo',
    [
        'alias_name',
        'alias',
    ],
)

SuffixMap = namedtuple(
    'SuffixMap',
    [
        'directory',
        'default_roles',
    ],
)

def generate_alias(component, role, target="install"):
    """Generate a scons alias for the component and role combination"""
    return "{target}-{component}{role}".format(
        target=target,
        component=component,
        role="" if role == "runtime" else "-" + role,
    )


def get_package_name(env, component, role, suffix=""):
    """Return the package file name for the component and role combination."""
    combination = (component, role)
    basename = env.subst(
        env[PACKAGE_ALIAS_MAP].get(
            combination,
            "{component}-{role}".format(component=component, role=role)
        )
    )
    return '{prefix}{basename}'.format(basename=basename, prefix=env.subst(env[PACKAGE_PREFIX]))


def get_dependent_actions(
        components,
        roles,
        non_transitive_roles,
        node,
        cb=None,
):
    """
    Check if node is a transitive dependency of components and roles

    If cb is not None and is callable then it will be called with all
    the arguments that get_dependent_actions was called with (except
    for cb itself) as well as the results of node_roles and the
    aib_install_actions that this function would have returned. The
    return of cb should be the dependent actions. This allows cb to
    access the results of scanning and modify the returned results via
    additional filtering.

    Returns the dependent actions.
    """
    actions = getattr(node.attributes, INSTALL_ACTIONS, None)
    if not actions:
        return []

    # Determine if the roles have any overlap with non_transitive_roles
    #
    # If they are overlapping then that means we can't transition to a
    # new role during scanning.
    if "base" not in roles:
        can_transfer = (
            non_transitive_roles
            and roles.isdisjoint(non_transitive_roles)
        )
    else:
        can_transfer = True

    node_roles = {
        role for role
        in getattr(node.attributes, "aib_roles", set())
        if role != "meta"
    }
    if (
        # TODO: make the "always transitive" roles configurable
        "base" not in node_roles
        # If we are not transferrable
        and not can_transfer
        # Checks if we are actually crossing a boundry
        and node_roles.isdisjoint(roles)
    ):
        return []

    if cb is not None and callable(cb):
        return cb(
            components,
            roles,
            non_transitive_roles,
            node,
            node_roles,
            actions,
        )
    return actions


def scan_for_transitive_install(node, env, cb=None):
    """Walk the children of node finding all installed dependencies of it."""
    results = []
    install_sources = node.sources
    # Filter out all
    components = {
        component for component
        in getattr(node.sources[0].attributes, COMPONENTS, set())
        if component != "all"
    }
    roles = {
        role for role
        in getattr(node.sources[0].attributes, ROLES, set())
        if role != "meta"
    }
    # TODO: add fancy configurability
    non_transitive_roles = {role for role in roles if role == "runtime"}
    for install_source in install_sources:
        install_executor = install_source.get_executor()
        if not install_executor:
            continue
        install_targets = install_executor.get_all_targets()
        if not install_targets:
            continue
        for install_target in install_targets:
            grandchildren = install_target.children()
            for grandchild in grandchildren:
                results.extend(
                    get_dependent_actions(
                        components,
                        roles,
                        non_transitive_roles,
                        grandchild,
                        cb=cb,
                    )
                )

    # Produce deterministic output for caching purposes
    results = sorted(results, key=str)
    return results


def collect_transitive_files(env, source):
    """Collect all transitive files for source where source is a list of either Alias or File nodes."""
    files = []

    for s in source:
        if isinstance(s, SCons.Node.FS.File):
            files.append(s)
            continue
        else:
            files.extend(collect_transitive_files(env, s.children()))

    return files


def tarball_builder(target, source, env):
    """Build a tarball of the AutoInstall'd sources."""
    if not source:
        return
    if not isinstance(source, list):
        source = [source]
    else:
        source = env.Flatten(source)

    transitive_files = collect_transitive_files(env, source)
    common_ancestor = env.Dir("$DEST_DIR").get_abspath()
    paths = {file.get_abspath() for file in transitive_files}
    relative_files = [os.path.relpath(path, common_ancestor) for path in paths]
    # Target name minus the .gz
    # TODO: $PKGDIR support
    tar_name = str(target[0])
    tar_cmd = SCons.Action._subproc(
        env,
        shlex.split(
            "tar -P -czf {tarball} -C {ancestor} {files}".format(
                tarball=tar_name,
                ancestor=common_ancestor,
                files=" ".join(relative_files),
            )
        ),
    )
    tar_cmd.wait()


def package_builder_string_func(target, source, env):
    """Print a human-friendly string when package builders are called."""
    alias_name = str(source[0])
    split = alias_name.split("-")
    component = "-".join(split[1:-1])
    # It's a runtime role so the role is missing
    if not component:
        component = split[-1]
        role = "runtime"
    else:
        role = split[-1]
    return "Building package {} from component {} and role {}".format(
        target[0],
        component,
        role
    )


def auto_install(env, target, source, **kwargs):
    """Auto install builder."""
    source = [env.Entry(s) for s in env.Flatten([source])]
    roles = {
        kwargs.get(PRIMARY_ROLE),
        # The 'meta' tag is implicitly attached as a role.
        "meta",
    }

    if kwargs.get(ROLES) is not None:
        roles = roles.union(set(kwargs[ROLES]))

    component = kwargs.get(PRIMARY_COMPONENT)
    if (
            component is not None
            and (not isinstance(component, str)
                 or " " in component)
    ):
        raise Exception(
            "AIB_COMPONENT must be a string and contain no whitespace."
        )

    components = {
        component,
        # The 'all' tag is implicitly attached as a component
        "all",
    }
    # Some tools will need to create multiple components so we add
    # this "hidden" argument that accepts a set or list.
    #
    # Use get here to check for existence because it is rarely
    # ommitted as a kwarg (because it is set by the default emitter
    # for all common builders), but is often set to None.
    if kwargs.get(COMPONENTS) is not None:
        components = components.union(set(kwargs[COMPONENTS]))

    # Remove false values such as None or ""
    roles = {role for role in roles if role}
    components = {component for component in components if component}

    actions = []

    for s in source:
        s.attributes.keep_targetinfo = 1
        setattr(s.attributes, COMPONENTS, components)
        setattr(s.attributes, ROLES, roles)

        target = env.Dir(target)
        action = env.Install(
            target=target,
            source=s,
        )

        setattr(
            s.attributes,
            INSTALL_ACTIONS,
            action if isinstance(action, (list, set)) else [action]
        )
        actions.append(action)


    actions = env.Flatten(actions)
    for component, role in itertools.product(components, roles):
        alias_name = generate_alias(component, role)
        alias = env.Alias(alias_name, actions)
        setattr(alias[0].attributes, COMPONENTS, components)
        setattr(alias[0].attributes, ROLES, roles)
        if role != "base":
            env.Depends(alias, env.Alias(generate_alias(component, "base")))
        if not (component == "common" and role == "base"):
            env.Depends(alias, env.Alias("install-common-base"))
        env[ALIAS_MAP][component][role] = RoleInfo(
            alias_name=alias_name,
            alias=alias,
        )

    return actions


def finalize_install_dependencies(env):
    """Generates package aliases and wires install dependencies."""
    common_rolemap = env[ALIAS_MAP].get("common")
    default_rolemap = env[ALIAS_MAP].get("default")

    if default_rolemap and "runtime" in default_rolemap:
        env.Alias("install", "install-default")
        env.Default("install")

    installed_files = env.FindInstalledFiles()

    for component, rolemap in env[ALIAS_MAP].items():
        for role, info in rolemap.items():

            aliases = [info.alias]
            if common_rolemap and component != "common" and role in common_rolemap:
                env.Depends(info.alias, common_rolemap[role].alias)
                aliases.extend(common_rolemap[role].alias)

            for dependency in env[ROLE_DEPENDENCIES].get(role, []):
                dependency_info = rolemap.get(dependency, [])
                if dependency_info:
                    env.Depends(info.alias, dependency_info.alias)

            pkg_name = get_package_name(env, component, role)
            tar = env.TarBall(
                "{}.tar.gz".format(pkg_name),
                source=aliases,
                AIB_COMPONENT=component,
                AIB_ROLE=role,
            )
            env.NoCache(tar)
            tar_alias = generate_alias(component, role, target="tar")
            env.Alias(tar_alias, tar)


def auto_install_emitter(target, source, env):
    """When attached to a builder adds an appropriate AutoInstall to that Builder."""
    for t in target:
        entry = env.Entry(t)
        suffix = entry.get_suffix()
        if env.get("AIB_IGNORE", False):
            continue
        auto_install_mapping = env[SUFFIX_MAP].get(suffix)
        if auto_install_mapping is not None:
            env.AutoInstall(
                auto_install_mapping.directory,
                entry,
                AIB_COMPONENT=env.get(PRIMARY_COMPONENT),
                AIB_ROLE=env.get(PRIMARY_ROLE),
                AIB_ROLES=auto_install_mapping.default_roles,
                AIB_COMPONENTS_EXTRA=env.get(COMPONENTS),
            )
    return (target, source)


def extend_attr(node, attr, value):
    """Set attr to value or extend the set if it exists."""
    existing = getattr(node.attributes, attr, False)
    if existing:
        value = existing.union(value)
    setattr(node.attributes, attr, value)


def add_suffix_mapping(env, source, target=None):
    """Map the suffix source to target"""
    if isinstance(source, str):
        if target not in AVAILABLE_ROLES:
            raise Exception(
                "target {} is not a known role. Available roles are {}".format(
                    target, AVAILABLE_ROLES
                )
            )
        env[SUFFIX_MAP][env.subst(source)] = target

    if not isinstance(source, dict):
        raise Exception("source must be a dictionary or a string")

    for _, mapping in source.items():
        for role in mapping.default_roles:
            if role not in AVAILABLE_ROLES:
                raise Exception(
                    "target {} is not a known role. Available roles are {}".format(
                        target, AVAILABLE_ROLES
                    )
                )

    env[SUFFIX_MAP].update({env.subst(key): value for key, value in source.items()})


def add_package_name_alias(env, source=None, target=None, name="", component=None, role=None):
    """Add a package name mapping for the combination of component and role."""
    if not name:
        raise Exception("when setting a package name alias must provide a name parameter")
    if source is not None and component is None:
        component = source
    if target is not None and role is None:
        role = target
    env[PACKAGE_ALIAS_MAP][(component, role)] = name


def suffix_mapping(env, source=False, target=False, **kwargs):
    """Generate a SuffixMap object from source and target."""
    return SuffixMap(
        directory=source if source else kwargs.get("directory"),
        default_roles=target if target else kwargs.get("default_roles"),
    )


def _aib_debugdir(source, target, env, for_signature):
    for s in source:
        # TODO: Dry this with auto_install_emitter
        # TODO: We shouldn't need to reach into the attributes of the debug tool like this.
        origin = getattr(s.attributes, "debug_file_for", None)
        oentry = env.Entry(origin)
        osuf = oentry.get_suffix()
        return env[SUFFIX_MAP].get(osuf)[0]


def exists(_env):
    """Always activate this tool."""
    return True


def list_components(env, **kwargs):
    """List registered components for env."""
    print("Known AIB components:")
    for key in env[ALIAS_MAP]:
        print("\t", key)


def list_targets(env, **kwargs):
    """List AIB generated targets for env."""
    print("Generated AIB targets:")
    for _, rolemap in env[ALIAS_MAP].items():
        for _, info in rolemap.items():
            print("\t", info.alias[0].name)


def generate(env):  # pylint: disable=too-many-statements
    """Generate the auto install builders."""
    bld = SCons.Builder.Builder(
        action=SCons.Action.Action(
            tarball_builder, 
            package_builder_string_func,
        )
    )
    env.Append(BUILDERS={"TarBall": bld})

    env["PREFIX_BIN_DIR"] = "$INSTALL_DIR/bin"
    env["PREFIX_LIB_DIR"] = "$INSTALL_DIR/lib"
    env["PREFIX_DOC_DIR"] = "$INSTALL_DIR/share/doc"
    env["PREFIX_INCLUDE_DIR"] = "$INSTALL_DIR/include"
    env["PREFIX_SHARE_DIR"] = "$INSTALL_DIR/share"
    env["PREFIX_DEBUG_DIR"] = _aib_debugdir
    env[PACKAGE_PREFIX] = env.get(PACKAGE_PREFIX, "")
    env[SUFFIX_MAP] = {}
    env[PACKAGE_ALIAS_MAP] = {}
    env[ALIAS_MAP] = defaultdict(dict)
    env[ROLE_DEPENDENCIES] = {
        "debug": [
            "runtime",
        ],
        "dev": [
            "runtime",
            "common",
        ],
        "meta": [
            "dev",
            "runtime",
            "common",
            "debug",
        ],
        "runtime": [
            "common",
        ],
    }

    env.AddMethod(suffix_mapping, "SuffixMap")
    env.AddMethod(add_suffix_mapping, "AddSuffixMapping")
    env.AddMethod(add_package_name_alias, "AddPackageNameAlias")
    env.AddMethod(auto_install, "AutoInstall")
    env.AddMethod(finalize_install_dependencies, "FinalizeInstallDependencies")
    env.Tool("install")

    env.Alias("list-aib-components", [], [list_components])
    env.AlwaysBuild("list-aib-components")

    env.Alias("list-aib-targets", [], [list_targets])
    env.AlwaysBuild("list-aib-targets")

    for builder in ["Program", "SharedLibrary", "LoadableModule", "StaticLibrary"]:
        builder = env["BUILDERS"][builder]
        base_emitter = builder.emitter
        new_emitter = SCons.Builder.ListEmitter([
            base_emitter,
            auto_install_emitter,
        ])
        builder.emitter = new_emitter

    base_install_builder = install.BaseInstallBuilder
    assert base_install_builder.target_scanner is None

    base_install_builder.target_scanner = SCons.Scanner.Scanner(
        function=scan_for_transitive_install, path_function=None
    )
