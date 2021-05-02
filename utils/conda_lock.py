"""

Python script to get platform-independent environment.yml file with all dependencies

"""

import argparse
import subprocess
import sys
import uuid
from distutils.core import run_setup
from pathlib import Path
from types import TracebackType
from typing import Optional, List, Type, Union, Tuple, Dict

import yaml
from setuptools.config import read_configuration


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Get platform-independent full environment.yml file")
    parser.add_argument('env_file', help="path to the env file")
    return parser


def read_file(file_path: str) -> str:
    with open(file_path, 'r') as i:
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


def is_local_dep(dep: str) -> bool:
    return "-r " not in dep and ("-e " in dep or '..' in dep or '/' in dep or '\\' in dep)


def get_channels(env: dict) -> List[str]:
    return env["channels"] if "channels" in env else []


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


def lock_env(env_file: str) -> str:
    with RandomCondaEnv(env_file) as conda_env:
        return subprocess.check_output(["conda", "env", "export", "-n", conda_env.name, "--no-builds"],
                                       universal_newlines=True)


def is_on_platform(pkg: str, platform: str, channels: Optional[List[str]] = None) -> bool:
    args = ["conda", "search", "--platform", platform]
    for channel in channels:
        args.extend(["-c", channel])
    args.append(pkg)
    # return non-zero if package is not available on given platform
    return subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def is_independent(pkg: str, channels: Optional[List[str]] = None, platforms: Optional[List[str]] = None) -> bool:
    if platforms is None:
        platforms = ["linux-64", "osx-64", "win-64"]
    # platform independent if marked as noarch or available on all platforms
    return is_on_platform(pkg, "noarch", channels) or all(is_on_platform(pkg, p, channels) for p in platforms)


def pkg(dep: str, base_dir: str = '.') -> str:
    if not is_local_dep(dep):
        return dep.partition('=')[0]
    else:
        p = Path(dep.strip().replace("-e ", '').strip())
        if not p.is_absolute():
            p = Path(base_dir) / p
        p = p.resolve()
        if (p / "setup.cfg").exists():
            return read_configuration(p.resolve() / "setup.cfg")['metadata']['name']
        else:
            return run_setup(p / "setup.py", stop_after='init').metadata.name


def version(dep: str) -> Optional[str]:
    return dep.rpartition('=')[2] if '=' in dep else None


def merge_deps(deps_a: List[str], deps_b: List[str]) -> List[str]:
    def to_dict(deps: List[str]) -> Dict[str, str]:
        return {pkg(d): version(d) for d in deps}

    deps_a, deps_b = to_dict(deps_a), to_dict(deps_b)
    merged_deps = {**deps_a, **deps_b}
    return [f"{k}=={v}" if v else f"{k}" for k, v in merged_deps.items()]


def replace_deps(env: dict, conda_deps: List[str], pip_deps: List[str]) -> dict:
    deps: List[Union[str, dict]] = conda_deps
    if pip_deps:
        deps.append({"pip": pip_deps})
    env["dependencies"] = deps
    return env


def main() -> Optional[int]:
    args = get_parser().parse_args()

    # analyze original env
    env_dict = to_dict(read_file(args.env_file))
    conda_deps, pip_deps = get_dependencies(env_dict)
    channels = get_channels(env_dict)  # we need channels from original file, because export can reorder them

    # create temp env and export dependencies from it
    env_locked_dict = to_dict(lock_env(args.env_file))
    conda_locked_deps, pip_locked_deps = get_dependencies(env_locked_dict)

    # get only platform-independent conda dependencies (pip can't be checked that way)
    conda_locked_deps = [x for x in conda_locked_deps if is_independent(x, channels=channels)]
    # filter out local dependencies
    pip_local_deps = [x for x in pip_deps if is_local_dep(x)]
    pip_local_deps_pkgs = [pkg(x, base_dir=Path(args.env_file).parent) for x in pip_local_deps]
    pip_locked_deps = [x for x in pip_locked_deps if pkg(x) not in pip_local_deps_pkgs]

    # merge conda dependencies (it's necessary if you want to force platform-dependent dependency)
    new_conda_deps = merge_deps(conda_deps, conda_locked_deps)
    # get new env file
    new_env_dict = replace_deps(env_dict, new_conda_deps, pip_locked_deps + pip_local_deps)

    print(to_yaml(new_env_dict))


if __name__ == '__main__':
    sys.exit(main())
