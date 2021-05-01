"""

Python script to get requirements.txt file with all dependencies

"""

import argparse
import contextlib
import subprocess
import sys
import uuid
from tempfile import NamedTemporaryFile
from types import TracebackType
from typing import ContextManager, TextIO, Optional, Type, List

import yaml


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Get full requirements.txt file")
    parser.add_argument('--python', help="python version to use")
    parser.add_argument('--pip', help="pip version to use")
    parser.add_argument('req_file', nargs='?', default='-',
                        help="path to the requirements.txt file (when not given, reads content directly from stdin)")
    return parser


@contextlib.contextmanager
def open_input(filename: str) -> ContextManager[TextIO]:
    if filename == '-':
        yield sys.stdin
    else:
        with open(filename, 'r') as f:
            yield f


def read_req(req_file_path: str) -> str:
    with open_input(req_file_path) as i:
        return i.read()


def filter_comments(req: str) -> str:
    return ''.join([line for line in req.splitlines(keepends=True) if not line.startswith('#')])


def to_dict(env: str) -> dict:
    return yaml.safe_load(env)


def to_yaml(env: dict) -> str:
    # custom dumper for indentation
    class MyDumper(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super(MyDumper, self).increase_indent(flow, False)

    return yaml.dump(env, Dumper=MyDumper, sort_keys=False, default_flow_style=False)


def get_env(req: str, python: Optional[str] = None, pip: Optional[str] = None) -> str:
    python_str = f"python=={python}" if python else "python"
    pip_str = f"pip=={pip}" if pip else "pip"
    env = {
        "dependencies": [
            python_str,
            pip_str,
            {"pip": req.splitlines()}
        ]
    }
    return to_yaml(env)


def pip_dependencies(env: dict) -> List[str]:
    if "dependencies" in env:
        pip_dict = next((x for x in env["dependencies"] if isinstance(x, dict) and "pip" in x), None)
        if pip_dict:
            return pip_dict["pip"]
    return []


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


def get_full_req(env: str) -> str:
    # create temporary .yml file
    with NamedTemporaryFile(mode='wt', suffix=".yml") as tfile:
        tfile.write(env)
        tfile.flush()
        # create temporary conda environment with given .yml and capture export
        with RandomCondaEnv(tfile.name) as conda_env:
            out = subprocess.check_output(["conda", "env", "export", "-n", conda_env.name, "--no-builds"],
                                          universal_newlines=True)

    # get only pip dependencies
    return "\n".join(pip_dependencies(to_dict(out)))


def main() -> Optional[int]:
    args = get_parser().parse_args()
    req = filter_comments(read_req(args.req_file))
    # create .yml file content
    env = get_env(req, args.python, args.pip)
    # create temporary environment from .yml content and export pip dependencies from it
    full_req = get_full_req(env)
    print(full_req)


if __name__ == '__main__':
    sys.exit(main())
