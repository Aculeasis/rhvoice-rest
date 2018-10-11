#!/bin/bash

echo "Setting trap PID $$"
trap cleanup INT TERM

cleanup() {
    echo 'stopping...'
    APP="$(pgrep 'python' -a | grep 'app.py' | awk '{print $1}')"
    kill -TERM "$APP"
    wait
    echo "stop"
    exit 0
}

if [ -f /usr/local/etc/RHVoice/RHVoice.conf ] && [ ! -L /usr/local/etc/RHVoice/RHVoice.conf ]; then
    if [ ! -f /opt/cfg/RHVoice.conf ]; then
        mv /usr/local/etc/RHVoice/RHVoice.conf /opt/cfg/RHVoice.conf
    fi
    ln -fs /opt/cfg/RHVoice.conf /usr/local/etc/RHVoice/RHVoice.conf
fi

if [ -f /opt/LIBRARY_PATH ]; then
    LIBRARY_PATH=$(head -1 /opt/LIBRARY_PATH)
    echo "Set LD_LIBRARY_PATH=$LIBRARY_PATH"
    export LD_LIBRARY_PATH="$LIBRARY_PATH"
fi

if [ -f /opt/app.py ]; then
    python3 -u /opt/app.py &
fi

wait
