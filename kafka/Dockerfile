FROM debian:10.11-slim AS build
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes \
    netcat=1.10*  && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM bitnami/kafka:3.0.0-debian-10-r85
COPY --from=build /bin/nc /bin/nc
