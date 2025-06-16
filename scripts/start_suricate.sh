#!/bin/bash

export HOME=/discos-sw/discos/
export PATH="/alma/ACS-2021DEC/pyenv/shims:/alma/ACS-2021DEC/pyenv/bin:$PATH"
export PYENV_ROOT="/alma/ACS-2021DEC/pyenv"
export LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib64:/usr/lib64"
source /discos-sw/discos/.bashrc

exec /alma/ACS-2021DEC/pyenv/shims/suricate-server start
