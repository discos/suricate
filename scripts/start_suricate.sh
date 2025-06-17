#!/bin/bash

export HOME=/discos-sw/discos/
export PYENV_ROOT="/alma/ACS-2021DEC/pyenv"
export PATH="$PYENV_ROOT/shims:/alma/ACS-2021DEC/pyenv/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib64:/usr/lib64"
source "$HOME/.bashrc"

"$PYENV_ROOT/shims/suricate-server" start & PID1=$!
"$PYENV_ROOT/shims/rqworker" -P "$HOME/suricate/suricate discos-api" & PID2=$!

wait $PID1 $PID2
