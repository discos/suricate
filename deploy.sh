#!/bin/bash

set -e  # Stop the script if any command fails

# Every 5 minutes, set the sudo timeout (in background)
sudo -v
( while true; do sleep 300; sudo -n -v; done ) &
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

# Go back to home
cd ~

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

# Create the redis system user if it doesn't exist
if ! id "redis" &>/dev/null; then
  sudo adduser --system --no-create-home redis
else
  echo "User 'redis' already exists, skipping creation."
fi

# Configure redis
cd ~/suricate
sudo cp templates/redis.conf /etc/redis.conf

# Create the systemd service file for Redis
cd ~/suricate
sudo cp startup/redis.service /etc/systemd/system/redis.service

# Reload systemd and enable Redis
sudo systemctl daemon-reload
sudo systemctl enable redis.service
sudo service redis start

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

# Reload systemd and enable Suricate
cd ~/suricate
sudo cp scripts/start_suricate.sh /usr/local/bin/start_suricate.sh
sudo cp scripts/stop_suricate.sh /usr/local/bin/stop_suricate.sh
sudo cp startup/suricate.service /etc/systemd/system/suricate.service
sudo systemctl daemon-reload
sudo systemctl enable suricate.service

# Install DISCOS simulators
cd ~
git clone https://github.com/discos/simulators.git
cd simulators
pip install .

# Optional: start the RQ worker manually (commented)
# rqworker -P suricate/ discos-api

# Start discos simulators
# discos-simulators start

# Start discos
# discosup

kill $SUDO_KEEP_ALIVE_PID
sudo reboot
