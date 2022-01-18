FROM python:3.10.1-slim-bullseye as build
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes \
    gcc=4:10.2.1* \
    libpython3-dev=3.9.2* \
    python3-pip=20.3.4* && \
    pip3 install --no-cache-dir pipenv==2022.1.8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM build as build-venv
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PIPENV_VENV_IN_PROJECT=1
COPY ./Pipfile* /
RUN pipenv install --deploy

FROM python:3.10.1-slim-bullseye
RUN useradd non-root-user
USER non-root-user
WORKDIR /api
COPY --from=build-venv /.venv /venv
COPY src /api/src
ENTRYPOINT [ "/venv/bin/python3.10" ]
CMD [ "-m", "src.main" ]
