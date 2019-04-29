# TODO: Filter child chains by role (install bin/foo should not install lib/dep.debug)
# TODO: Add test tag automatically for unit tests, etc.
# TODO: Test tag still leaves things in the runtime component
# TODO: But meta doesn't depend on test! Should it though?
# TODO: How should debug info work for tests?
# TODO: destdir vs prefix (what about --install-sandbox?)
# TODO: Versioned libraries
# TODO: library dependency chaining for windows dynamic builds, static dev packages
# TODO: Injectible component dependencies (jscore -> resmoke, etc.)
# TODO: Distfiles and equivalent for the dist target
# TODO: Handle chmod state
# TODO: tarfile generation
# TODO: Installing resmoke and configurations
# TODO: package decomposition
# TODO: Install/package target help text
# TODO: implement sdk_headers
# TODO: Namedtuple for alias_map

import os
import shlex
import itertools
from collections import defaultdict, namedtuple

import SCons
from SCons.Tool import install


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
    return "{target}-{component}{role}"\
        .format(
            target=target,
            component=component,
            role="" if role == "runtime" else "-" + role,
        )


def tarball_builder(target, source, env):
    """Build a tarball using the lowest shared directory of sources as the root."""
    if not isinstance(source, list):
        source = [source]
    if not source:
        return
    paths = [file.get_abspath() for file in source]
    common_ancestor = os.path.commonprefix(paths)
    print("ancestor", common_ancestor)
    relative_files = [os.path.relpath(path, common_ancestor) for path in paths]
    SCons.Action._subproc(
        env,
        shlex.split('tar -cvf {tarball} -C {ancestor} {files}'
                    .format(
                        tarball=target[0],
                        ancestor=common_ancestor,
                        files=" ".join(relative_files),
                    )
        ),
    )


def exists(_env):
    """Always activate this tool."""
    return True


def generate(env):  # pylint: disable=too-many-statements
    """Generate the auto install builders."""


    bld = SCons.Builder.Builder(action = tarball_builder)
    env.Append(BUILDERS = {'TarBall': bld})
    
    env["INSTALLDIR_BINDIR"] = "$INSTALL_DIR/bin"
    env["INSTALLDIR_LIBDIR"] = "$INSTALL_DIR/lib"
    env["INSTALLDIR_INCLUDEDIR"] = "$INSTALL_DIR/include"

    role_dependencies = {
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

    env.Tool("install")

    # TODO: These probably need to be patterns of some sort, not just suffixes.
    # TODO: The runtime libs should be in runtime, the dev symlinks in dev
    suffix_map = {
        env.subst("$PROGSUFFIX"): SuffixMap(
            directory="$INSTALLDIR_BINDIR",
            default_roles=[
                "runtime",
            ]
        ),

        env.subst("$LIBSUFFIX"): SuffixMap(
            directory="$INSTALLDIR_LIBDIR",
            default_roles=[
                "dev",
            ]
        ),

        ".dll": SuffixMap(
            directory="$INSTALLDIR_BINDIR",
            default_roles=[
                "runtime",
            ]
        ),

        ".dylib": SuffixMap(
            directory="$INSTALLDIR_LIBDIR",
            default_roles=[
                "runtime",
                "dev",
            ]
        ),

        ".so": SuffixMap(
            directory="$INSTALLDIR_LIBDIR",
            default_roles=[
                "runtime",
                "dev",
            ]
        ),

        ".debug": SuffixMap(
            directory="$INSTALLDIR_DEBUGDIR",
            default_roles=[
                "debug",
            ]
        ),

        ".dSYM": SuffixMap(
            directory="$INSTALLDIR_LIBDIR",
            default_roles=[
                "runtime"
            ]
        ),

        ".lib": SuffixMap(
            directory="$INSTALLDIR_LIBDIR",
            default_roles=[
                "runtime"
            ]
        ),

        ".txt": SuffixMap(
            directory="$INSTALL_DIR",
            default_roles=[
                "runtime",
                "dev",
            ]
        ),

        ".h": SuffixMap(
            directory="$INSTALLDIR_INCLUDEDIR",
            default_roles=[
                "dev",
            ]
        ),

        # TODO: these are most assuredly wrong
        ".in": SuffixMap(
            directory="$INSTALLDIR_LIBDIR",
            default_roles=[
                "runtime",
                "dev",
            ]
        ),

        "THIR-PARTY-NOTICES": SuffixMap(
            directory="$INSTALL_DIR",
            default_roles=[
                "runtime",
                "dev",
            ]
        ),
    }

    def _aib_debugdir(source, target, env, for_signature):
        for s in source:
            # TODO: Dry this with auto_install_emitter
            # TODO: We shouldn't need to reach into the attributes of the debug tool like this.
            origin = getattr(s.attributes, "debug_file_for", None)
            oentry = env.Entry(origin)
            osuf = oentry.get_suffix()
            return suffix_map.get(osuf)[0]

    env["INSTALLDIR_DEBUGDIR"] = _aib_debugdir

    alias_map = defaultdict(dict)

    def auto_install(env, target, source, **kwargs):

        target = env.Dir(env.subst(target, source=source))

        # We want to make sure that the executor information stays
        # persisted for this node after it is built so that we can
        # access it in our install emitter below.
        source = list(map(env.Entry, env.Flatten([source])))

        roles = {
            kwargs.get("ROLE_TAG"),
            # The 'meta' tag is implicitly attached as a role.
            "meta",
        }

        if kwargs.get("ADDITIONAL_ROLES") is not None:
            roles = roles.union(set(kwargs["ADDITIONAL_ROLES"]))

        component_tag = kwargs.get("COMPONENT_TAG")
        if (
                component_tag is not None
                and (not isinstance(component_tag, str) or " " in component_tag)
        ):
            raise Exception(
                "COMPONENT_TAG must be a string and contain no whitespace."
            )
        components = {
            component_tag,
            # The 'all' tag is implicitly attached as a component
            "all",
        }
        # Some tools will need to create multiple components so we add
        # this "hidden" argument that accepts a set.
        if kwargs.get("ADDITIONAL_COMPONENTS") is not None:
            components.union(set(kwargs["ADDITIONAL_COMPONENTS"]))

        # Remove false values such as None
        roles = {role for role in roles if role}
        components = {component for component in components if component}
        for s in source:
            s.attributes.keep_targetinfo = 1
            if getattr(s.attributes, "components", False):
                s.attributes.components = s.attributes.components.union(components)
            else:
                s.attributes.components = components

            if getattr(s.attributes, "roles", False):
                s.attributes.roles = s.attributes.roles.union(roles)
            else:
                s.attributes.roles = roles

        actions = SCons.Script.Install(target=target, source=source)
        for s in source:
            print(s.attributes.__dict__)
            s.attributes.aib_install_actions = actions

        for component_tag, role_tag in itertools.product(components, roles):
            alias_name = generate_alias(component_tag, role_tag)
            alias = env.Alias(alias_name, actions)
            alias_map[component_tag][role_tag] = RoleInfo(
                alias_name=alias_name,
                alias=alias,
            )

        return actions

    env.AddMethod(auto_install, "AutoInstall")

    def finalize_install_dependencies(env):
        common_rolemap = alias_map.get("common", None)
        default_rolemap = alias_map.get("default", None)

        if default_rolemap and "runtime" in default_rolemap:
            env.Alias("install", "install-default")
            env.Default("install")

        for component, rolemap in alias_map.items():
            for role, info in rolemap.items():

                if common_rolemap and component != "common" and role in common_rolemap:
                    env.Depends(info.alias, common_rolemap[role].alias)

                for dependency in role_dependencies.get(role, []):
                    dependency_info = rolemap.get(dependency, [])
                    if dependency_info:
                        env.Depends(info.alias, dependency_info.alias)

        installedFiles = env.FindInstalledFiles()
        env.NoCache(installedFiles)

        for component, rolemap in alias_map.items():
            for role, info in rolemap.items():
                tar_alias = generate_alias(component, role, target="tar")
                tar_files = [
                    file for file in installedFiles
                    if component in getattr(file.attributes, "components", [])
                ]

                for file in installedFiles:
                    print(file)
                    print("attrs", file.attributes.__dict__)
                print("tar alias", tar_alias)
                tar = env.TarBall(
                    "{}.tar".format(tar_alias),
                    source=tar_files,
                    COMPONENT_TAG=component,
                    ROLE_TAG=role,
                )
                env.Alias(tar_alias, tar)
                env.Depends(tar, info.alias)

    env.AddMethod(finalize_install_dependencies, "FinalizeInstallDependencies")

    def auto_install_emitter(target, source, env):
        for t in target:
            entry = env.Entry(t)
            suffix = entry.get_suffix()
            if not suffix:
                # If not suffix check the suffix_map for the filename
                suffix = entry.name
            auto_install_mapping = suffix_map.get(suffix)
            if auto_install_mapping is not None:
                env.AutoInstall(
                    auto_install_mapping.directory,
                    entry,
                    COMPONENT_TAG=env.get("COMPONENT_TAG"),
                    ROLE_TAG=env.get("ROLE_TAG"),
                    ADDITIONAL_ROLES=auto_install_mapping.default_roles,
                    ADDITIONAL_COMPONENTS=env.get("ADDITIONAL_COMPONENTS"),
                )
        return (target, source)

    def add_emitter(builder):
        base_emitter = builder.emitter
        new_emitter = SCons.Builder.ListEmitter([
            base_emitter,
            auto_install_emitter,
        ])
        builder.emitter = new_emitter

    for builder in ["Program", "SharedLibrary", "LoadableModule", "StaticLibrary"]:
        builder = env["BUILDERS"][builder]
        add_emitter(builder)

    def scan_for_transitive_install(node, env, path=()):
        results = []
        install_sources = node.sources
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
                    actions = getattr(
                        grandchild.attributes, "aib_install_actions", None
                    )
                    if actions:
                        results.extend(actions)
        results = sorted(results, key=str)
        return results

    base_install_builder = install.BaseInstallBuilder
    assert base_install_builder.target_scanner is None

    base_install_builder.target_scanner = SCons.Scanner.Scanner(
        function=scan_for_transitive_install, path_function=None
    )
