FROM hseeberger/scala-sbt:11.0.13_1.6.1_2.12.15 AS build
COPY . .
RUN sbt assembly

FROM openjdk:11.0.13-jre-slim-bullseye
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes \
    kafkacat=1.6* \
    netcat=1.10*  && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN useradd non-root-user
USER non-root-user
WORKDIR /app
COPY ./entrypoint.sh /app/entrypoint.sh
COPY ./startup_scripts /app/startup_scripts
COPY --from=build /root/target /app/target
ENTRYPOINT [ "/app/entrypoint.sh" ]
