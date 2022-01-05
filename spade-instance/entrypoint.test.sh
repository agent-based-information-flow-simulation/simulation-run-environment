#!/bin/sh
/venv/bin/python3.10 -m coverage run \
--source=./src \
--omit="./src/*__init__.py","./src/main.py" \
-m pytest && \
/venv/bin/python3.10 -m coverage report -m "$@"
