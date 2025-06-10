#!/bin/bash

# Ask the sudo password once
Defaults timestamp_timeout=30
sudo -v

set -e  # Stop the script if any command fails

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

# Install and configure Suricate
cd ~/suricate
pip install -r requirements.txt
pip install -r testing_requirements.txt
pip install .

# Configure redis and Suricate
cd ~/suricate
sudo cp templates/redis.conf /etc/redis.conf
suricate-config -t srt

# Create the systemd service file for Redis and Suricate
cd ~/suricate
sudo cp startup/redis.service /etc/systemd/system/redis.service
sudo cp startup/suricate.service /etc/systemd/system/suricate.service

# Initialize Suricate database
cd ~/suricate/suricate
source .flaskenv
if [ ! -d migrations ]; then
  flask db init
fi

# Reload systemd and enable Redis
cd ~
sudo systemctl daemon-reload
sudo systemctl enable redis.service
sudo systemctl enable suricate.service
sudo reboot

# Optional: start the RQ worker manually (commented)
# rqworker -P suricate/ discos-api

# Start discos simulators
# discos-simulators start

# Start discos
# discosup
