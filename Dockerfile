FROM oven/bun:1
USER root
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN git init /opt/gbrain && git -C /opt/gbrain fetch --depth 1 https://github.com/garrytan/gbrain.git a5c1748f213289e11f033aea88f63ea5d2cf3603 && git -C /opt/gbrain checkout --detach FETCH_HEAD \
    && cd /opt/gbrain && bun install --frozen-lockfile && bun link \
    && gbrain --version
WORKDIR /opt/gbrain
