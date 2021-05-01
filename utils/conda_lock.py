"""

Python script to get platform-independent environment.yml file with all dependencies

"""

import argparse
import contextlib
import subprocess
import sys
import uuid
from tempfile import NamedTemporaryFile
from types import TracebackType
from typing import ContextManager, TextIO, Optional, List, Type, Union, Tuple, Dict

import yaml


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Get platform-independent full environment.yml file")
    parser.add_argument('env_file', nargs='?', default='-',
                        help="path to the env file (when not given, reads content directly from stdin)")
    return parser


@contextlib.contextmanager
def open_input(filename: str) -> ContextManager[TextIO]:
    if filename == '-':
        yield sys.stdin
    else:
        with open(filename, 'r') as f:
            yield f


def read_env(env_file_path: str) -> str:
    with open_input(env_file_path) as i:
        return i.read()


def conda_dependencies(env: dict) -> List[str]:
    if "dependencies" in env:
        return [x for x in env["dependencies"] if not isinstance(x, dict)]
    return []


def pip_dependencies(env: dict) -> List[str]:
    if "dependencies" in env:
        pip_dict = next((x for x in env["dependencies"] if isinstance(x, dict) and "pip" in x), None)
        if pip_dict:
            return pip_dict["pip"]
    return []


def get_dependencies(env: dict) -> Tuple[List[str], List[str]]:
    return conda_dependencies(env), pip_dependencies(env)


def to_dict(env: str) -> dict:
    return yaml.safe_load(env)


def to_yaml(env: dict) -> str:
    # custom dumper for indentation
    class MyDumper(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super(MyDumper, self).increase_indent(flow, False)

    return yaml.dump(env, Dumper=MyDumper, sort_keys=False, default_flow_style=False)


class CondaEnv:
    def __init__(self, env_file: str, name: str):
        self.env_file = env_file
        self.name = name

    def __enter__(self) -> 'CondaEnv':
        subprocess.run(["conda", "env", "create", "-f", self.env_file, "-n", self.name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self

    def __exit__(self, type: Optional[Type[BaseException]],
                 value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> bool:
        subprocess.run(["conda", "env", "remove", "-n", self.name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return False


class RandomCondaEnv(CondaEnv):
    def __init__(self, env_file: str):
        super().__init__(env_file, uuid.uuid4().hex)


def lock_env(env: str) -> str:
    # create temporary .yml file
    with NamedTemporaryFile(mode='wt', suffix=".yml") as tfile:
        tfile.write(env)
        tfile.flush()
        # create temporary conda environment with given .yml and capture export
        with RandomCondaEnv(tfile.name) as conda_env:
            out = subprocess.check_output(["conda", "env", "export", "-n", conda_env.name, "--no-builds"],
                                          universal_newlines=True)
        return out


def is_on_platform(pkg: str, platform: str, channels: Optional[List[str]] = None) -> bool:
    if channels is None:
        channels = ["defaults"]
    args = ["conda", "search", "--platform", platform]
    for channel in channels:
        args.extend(["-c", channel])
    args.append(pkg)
    # return non-zero if package is not available on given platform
    return subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def is_independent(pkg: str, channels: Optional[List[str]] = None, platforms: Optional[List[str]] = None) -> bool:
    if channels is None:
        channels = ["defaults"]
    if platforms is None:
        platforms = ["linux-64", "osx-64", "win-64"]
    # platform independent if marked as noarch or available on all platforms
    return is_on_platform(pkg, "noarch", channels) or all(is_on_platform(pkg, p, channels) for p in platforms)


def merge_deps(deps_a: List[str], deps_b: List[str]) -> List[str]:
    def to_dict(deps: List[str]) -> Dict[str, str]:
        return {d.partition('=')[0]: d.rpartition('=')[2] for d in deps}

    deps_a, deps_b = to_dict(deps_a), to_dict(deps_b)
    merged_deps = {**deps_a, **deps_b}
    return [f"{k}=={v}" for k, v in merged_deps.items()]


def replace_deps(env: dict, conda_deps: List[str], pip_deps: List[str]) -> dict:
    deps: List[Union[str, dict]] = conda_deps
    if pip_deps:
        deps.append({"pip": pip_deps})
    if "dependencies" in env:
        env["dependencies"] = deps
    return env


def main() -> Optional[int]:
    args = get_parser().parse_args()

    # analyze base env file
    old_env_dict = to_dict(read_env(args.env_file))
    old_conda_deps, old_pip_deps = get_dependencies(old_env_dict)

    # get whole env file from actual environment
    env_locked_dict = to_dict(lock_env(to_yaml(old_env_dict)))

    # merge base and new dependencies
    new_conda_deps = [x for x in conda_dependencies(env_locked_dict) if is_independent(x)]
    new_conda_deps = merge_deps(new_conda_deps, old_conda_deps)
    new_env_dict = replace_deps(old_env_dict, new_conda_deps, old_pip_deps)

    print(to_yaml(new_env_dict))


if __name__ == '__main__':
    sys.exit(main())
