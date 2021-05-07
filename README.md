<h1 align="center">pytemplate</h1>

<div align="center">

[![Running tests](https://github.com/spietras/python-template/actions/workflows/test.yml/badge.svg)](https://github.com/spietras/python-template/actions/workflows/test.yml)
[![Deploying docs](https://github.com/spietras/python-template/actions/workflows/docs.yml/badge.svg)](https://github.com/spietras/python-template/actions/workflows/docs.yml)

</div>

---

This ```README``` provides info about the development process.

For more info about the package itself see ```pytemplate/README.md```.

## Environment management

We are using [```conda```](https://conda.io) for environment management (and for installing ```poetry```). 
The major reason is that ```conda``` lets you specify ```python``` version and will install that version in the environment.
This ensures consistency between different instances (developers, CI, deployment).

The first step is of course to install [```conda```](https://conda.io).

To create an environment, run from project root:

```sh
conda env create -f environment.yml
```

And then activate it by:

```sh
conda activate pytemplate
```

Creating the environment is performed only once, but you need to activate it every time you start a new shell.

If the configuration file ```environment.yml``` changes, you can update the environment by:

```sh
conda env update -f environment.yml
```

## Package management

We are using [```poetry```](https://python-poetry.org) to manage our package and its dependencies. 
It's already installed in the environment.

To install the package, you need to ```cd``` into ```pytemplate``` directory and run:

```sh
poetry install --extras dev
```

This will download and install all package dependencies (including optional development ones) and install the package in editable mode.

Editable mode means that you don't have to reinstall the package if you change something in the code.
The changes are reflected automatically. 

However, you need to install the package again if you change something in its configuration (e.g. add a new dependency).
But more on that later.

If it's the first time installing the package, ```poetry``` will write specific versions of all packages to ```poetry.lock``` file.
This file should be committed to the repository, so other people can have the exact same versions of all dependencies.
It will work because ```poetry install``` checks if ```poetry.lock``` file is available and uses it if it is.

## Testing

We are using [```pytest```](https://pytest.org) for tests.
It's already installed in the environment, because it's a development-time dependency.
To start first write the tests and put them in ```pytemplate/tests```.

To execute the tests, run from project root:

```sh
pytest pytemplate
```

## Bulding docs

We are using [```mkdocs```](https://www.mkdocs.org) with [```material```](https://squidfunk.github.io/mkdocs-material) for building the docs.
It lets you write the docs in Markdown format and creates a nice webpage for them.

Docs should be placed in ```pytemplate/docs/docs```. 
They are pretty straightforward to write.

To build the docs, ```cd``` into ```pytemplate/docs``` and run:

```sh
mkdocs build
```

It will generate ```site``` directory with the webpage source.

## Adding new dependencies

If you need to add a new dependency, look into ```pyproject.toml``` file.
Add it to ```tool.poetry.dependencies``` section.
If it is a development-time dependency you need to mark it as optional and add it to the right groups in ```tool.poetry.extras```.

After that update the installation by running from ```pytemplate``` directory:

```sh
poetry update
```

This will install anything new in your environment and update the ```poetry.lock``` file.
Other people only need to run ```poetry install``` to adjust to the incoming changes in the ```poetry.lock``` file.

## Continuous Integration

When you push changes to remote, different Github Actions run to ensure project consistency.
There are defined workflows for testing on different platforms, deploying docs to Github Pages and testing Docker builds.

For more info see the files in ```.github/workflows``` directory and ```Actions``` tab on Github.

Generally if you see a red mark next to your commit on Github or a failing status on badges in ```README``` it means the commit broke something (or workflows themselves are broken).

## Docker

You can build a Docker image of the package (e.g. for deployment).
The build process in defined in ```Dockerfile``` and it's optimized to keep the size small.

To build the image, run from project root:

```sh
 docker build -t pytemplate .
```

To also run the container in one go, run:

```sh
docker build -t pytemplate . && docker run --rm -it pytemplate
```

## Jupyter

You can use [```jupyter```](https://jupyter.org) to experiment with the code and make some great visualizations or reports.

To launch ```jupyter lab``` environment, ```cd``` to ```notebooks``` (although you might do it as well from root if you want) and run:

```sh
jupyter lab
```

The developed package is installed in the environment so we can import it in the notebooks as any other package.

## Disclaimer: ```conda``` + ```poetry```

```poetry``` detects that it is inside a virtual environment and install all packages to that environment.
That's cool but on the other hand ```conda``` is not supervising any further modifications to the environment.
This means that ```poetry``` can change package versions that have been already accepted by ```conda``` and possibly break some constraints.

For example we install ```poetry``` in the environment (managed by ```conda```) and ```poetry``` depends on package ```X```, versions ```1.5``` and above.
Now let's say our package (managed by ```poetry```) also needs package ```X```, this time version ```1.4.0``` exclusively.
```poetry``` doesn't know about any constraints managed by ```conda``` and will happily install package ```X``` in version ```1.4.0```, thus breaking the constraints.
This can lead to ```poetry``` not working.

Fortunately the only "packages" on ```conda``` side are ```python``` and ```poetry``` and they have a rather small number of very specific dependencies.
The constraints are rather loose and hard to break in practice. Nevertheless, there is a risk.