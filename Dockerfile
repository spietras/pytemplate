FROM continuumio/miniconda3:4.9.2-alpine

# add bash, because it's not available by default on alpine
RUN apk add --no-cache bash

# update base environment (instead of creating new one to keep the image size small) and delete cache
# see: https://jcristharif.com/conda-docker-tips.html
# warning: for some reason conda can hang on "Executing transaction" for a couple of minutes
COPY environment.yml /tmp/environment.yml
RUN conda env update -n base -f /tmp/environment.yml \
    && conda clean -afy \
    && find /opt/conda/ -follow -type f -name '*.a' -delete \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete \
    && find /opt/conda/ -follow -type f -name '*.js.map' -delete

# "activate" environment for all commands (note: ENTRYPOINT is separate from SHELL)
SHELL ["conda", "run", "--no-capture-output", "/bin/bash", "-c"]

# add poetry files
COPY ./pytemplate/pyproject.toml ./pytemplate/poetry.lock /tmp/pytemplate/
WORKDIR /tmp/pytemplate

# install dependencies only (notice that no source code is present yet) and delete cache
RUN poetry install --no-root \
    && rm -rf ~/.cache/pypoetry

# add source and necessary files
COPY ./pytemplate/src/ /tmp/pytemplate/src/
COPY ./pytemplate/LICENSE ./pytemplate/README.md /tmp/pytemplate/

# build wheel by poetry and install by pip (to force non-editable mode)
RUN poetry build -f wheel \
    && pip install --no-cache-dir --find-links=dist pytemplate

ENTRYPOINT ["conda", "run", "--no-capture-output", "pytemplate"]