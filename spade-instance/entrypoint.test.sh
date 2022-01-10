#!/bin/sh
/venv/bin/python3.9 -m coverage run \
--source=./src \
--omit="./src/*__init__.py","./src/main.py" \
-m pytest -W ignore::DeprecationWarning && \
/venv/bin/python3.9 -m coverage report -m "$@"
