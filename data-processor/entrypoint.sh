#!/bin/bash
# env variables:
# - PROXY_REGISTRATION_ADDRESS
# - PROXY_REGISTRATION_BACKEND_DATA_PROCESSOR_NAME
# - PROXY_REGISTRATION_BACKEND_DATA_PROCESSOR_PORT
# - PROXY_REGISTRATION_MAX_RETRIES
# - PROXY_REGISTRATION_USER_NAME
# - PROXY_REGISTRATION_USER_PASSWORD

/api/startup_scripts/wait_for_db.sh && \
/api/startup_scripts/wait_for_proxy.sh && \
/venv/bin/python3.9 -u /api/startup_scripts/register_in_proxy.py \
    "${PROXY_REGISTRATION_ADDRESS}" \
    "${PROXY_REGISTRATION_USER_NAME}" \
    "${PROXY_REGISTRATION_USER_PASSWORD}" \
    "${PROXY_REGISTRATION_MAX_RETRIES}" \
    `cat /etc/hostname` \
    "${PROXY_REGISTRATION_BACKEND_DATA_PROCESSOR_NAME}" \
    "${PROXY_REGISTRATION_BACKEND_DATA_PROCESSOR_PORT}" && \
/venv/bin/python3.9 -m src.main
