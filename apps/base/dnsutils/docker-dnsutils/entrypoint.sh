#!/bin/bash

# Start iperf3 server in the background
iperf3 -s &

# Keep the container running
sleep infinity
