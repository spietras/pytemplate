"""Main script.

This module provides basic CLI entrypoint.

"""

import argparse
import sys

from pytemplate.subpackage.module import get_something


def get_arg_parser():
    parser = argparse.ArgumentParser(description="Simple app")
    return parser


def main():
    """Package entry point as console script."""

    args = get_arg_parser().parse_args()
    print(get_something())


if __name__ == '__main__':
    # entry point for "python -m"
    sys.exit(main())
