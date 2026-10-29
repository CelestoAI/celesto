ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    busybox-static docker.io xfsprogs util-linux iproute2 iptables ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY guest-init /init
RUN chmod 0755 /init
