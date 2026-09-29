#!/bin/sh
# Start the controller in Celesto's coding-agent image, which has no systemd.
set -eu
cd /root/celesto/examples/github-actions-runner-controller
mkdir -p /root/celesto-ci
if [ -f /root/celesto-ci/controller.pid ] && kill -0 "$(cat /root/celesto-ci/controller.pid)" 2>/dev/null; then
    echo "Controller is already running as PID $(cat /root/celesto-ci/controller.pid)"
    exit 0
fi
setsid sh -c '
    while :; do
        cd /root/celesto/examples/github-actions-runner-controller
        set -a
        . /root/celesto-ci/controller.env
        set +a
        uv run python controller.py
        sleep 10
    done
' </dev/null >>/root/celesto-ci/controller.log 2>&1 &
echo "$!" >/root/celesto-ci/controller.pid
echo "Controller started as PID $(cat /root/celesto-ci/controller.pid)"
