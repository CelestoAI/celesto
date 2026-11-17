ARG BASE_IMAGE=ubuntu:24.04

# Build the nested-VM probe in a separate stage so the guest image stays
# free of compilers. Static, so it needs no libraries at boot. x86_64 only
# (the probe's guest code is x86); other architectures get no probe.
FROM ${BASE_IMAGE} AS kvm-smoke
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    gcc libc6-dev linux-libc-dev \
    && rm -rf /var/lib/apt/lists/*
COPY kvm-smoke.c /src/kvm-smoke.c
RUN mkdir -p /out && if [ "$(uname -m)" = x86_64 ]; then \
        gcc -static -O2 -Wall -Werror -o /out/kvm-smoke /src/kvm-smoke.c; \
    fi

FROM ${BASE_IMAGE}
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    busybox-static docker.io xfsprogs util-linux iproute2 iptables ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=kvm-smoke /out/ /usr/local/bin/
COPY guest-init /init
RUN chmod 0755 /init
