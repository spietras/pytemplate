<h1 align="center">pytemplate</h1>

<div align="center">

[![Running tests](https://github.com/spietras/python-template/actions/workflows/test.yml/badge.svg)](https://github.com/spietras/python-template/actions/workflows/test.yml)
[![Deploying docs](https://github.com/spietras/python-template/actions/workflows/docs.yml/badge.svg)](https://github.com/spietras/python-template/actions/workflows/docs.yml)

</div>

---

This is a simple example package.

It lets you easily accomplish the following things:

- [x] **nothing**

But at least it shows some opinionated best practices about python projects.

## Installing

Using ```pip```<sup>*</sup>:

```sh
pip install pytemplate
```

<sup><sup>* assuming the authors bothered to release the package on PyPI...</sup></sup>

## Usage as a library

**Very** useful example:

```python
from pytemplate.subpackage.module import identity

x = 1
assert x is identity(x)
```

## Usage as a command line tool

```sh
$ pytemplate
Hello World.
```