#!/bin/bash

# Stop the script if any command fails
set -e

# Every 4 minutes, keep alive sudo (in background)
sudo -v
( while true; do sleep 240; sudo -n -v; done ) &
SUDO_KEEP_ALIVE_PID=$!

# Go to the home directory
cd ~

# Clone and install DISCOS master for SRT
if [ ! -d master-srt ]; then
  discos-get master -s SRT
  source ~/.bashrc
  cd master-srt/SystemMake/
  make all install
fi

# Install redis 7.0.15, only if it's not already installed
cd ~
REDIS_VERSION=$(redis-server --version 2>/dev/null \
  | awk '{for(i=1;i<=NF;i++) if($i ~ /^v=/) print substr($i,3)}')

if [[ "$REDIS_VERSION" != "7.0.15" ]]; then
  # Download Redis only if the archive doesn't already exist
  if [ ! -f redis-7.0.15.tar.gz ]; then
    wget https://download.redis.io/releases/redis-7.0.15.tar.gz
  fi
  
  # Extract and build Redis
  tar xzf redis-7.0.15.tar.gz
  cd redis-7.0.15/
  make clean
  make BUILD_WITH_LTO=no
  sudo make install
fi

# Create the redis system user if it doesn't exist

if ! id "redis" &>/dev/null; then
  sudo adduser --system --no-create-home redis
else
  echo "User 'redis' already exists, skipping creation."
fi

# Configure redis
cd ~/suricate
sudo mkdir -p /var/lib/redis
sudo chown redis:redis /var/lib/redis
sudo chmod 750 /var/lib/redis
sudo cp templates/redis.conf /etc/redis.conf

# Create the systemd service file for Redis
cd ~/suricate
sudo cp startup/redis.service /etc/systemd/system/redis.service

# Reload systemd, enable and start Redis
sudo systemctl daemon-reload
sudo systemctl enable redis.service
sudo service redis start

# Make logging working also with older Python versions
FILE="$PYENV_ROOT/versions/3.9.4/lib/python3.9/logging/__init__.py"
sed -i 's/^#    _srcfile = None/_srcfile = None/' "$FILE" || true

# Install and configure Suricate
cd ~/suricate
pip install -r requirements.txt
pip install -r testing_requirements.txt
pip install .
suricate-config -t srt
cd ~/suricate/suricate
source .flaskenv
if [ ! -d migrations ]; then
  flask db init
fi

# Configure systemd for Suricate
cd ~/suricate
sudo cp scripts/start_suricate.sh /usr/local/bin/start_suricate.sh
sudo cp scripts/stop_suricate.sh /usr/local/bin/stop_suricate.sh
sudo cp startup/suricate.service /etc/systemd/system/suricate.service
sudo systemctl daemon-reload
sudo systemctl enable suricate.service

# Install DISCOS simulators
cd ~
if [ ! -d simulators ]; then
  git clone https://github.com/discos/simulators.git
  cd simulators
  pip install .
fi

kill $SUDO_KEEP_ALIVE_PID
sudo reboot
