FROM python:3.9.9-slim-bullseye as build
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes \
    git=1:2.30.2* \
    python3-pip=20.3.4* \
    gcc=4:10.2.1* \
    libpython3-dev=3.9.2* && \
    pip3 install --no-cache-dir pipenv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM build as build-venv
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PIPENV_VENV_IN_PROJECT=1
COPY ./Pipfile* /
RUN pipenv install --deploy

FROM python:3.9.9-slim-bullseye
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes \
    kafkacat=1.6* \
    netcat=1.10*  && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN useradd non-root-user
USER non-root-user
WORKDIR /api
COPY startup_scripts /api/startup_scripts
COPY entrypoint.sh /api/entrypoint.sh
COPY --from=build-venv /.venv /venv
COPY src /api/src
ENTRYPOINT [ "/api/entrypoint.sh" ]
