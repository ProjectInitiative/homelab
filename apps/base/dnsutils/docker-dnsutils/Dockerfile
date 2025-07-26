FROM debian:bookworm-slim

# Install basic utilities and iperf3
RUN apt-get update && apt-get install -y \
    curl \
    dnsutils \
    iperf3 \
    iproute2 \
    iputils-ping \
    net-tools \
    procps \
    telnet \
    traceroute \
    && rm -rf /var/lib/apt/lists/*

# Copy the entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["entrypoint.sh"]

# A simple default command
CMD ["sleep", "infinity"]

