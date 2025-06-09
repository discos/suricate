#!/bin/bash

set -e  # Stop the script if any command fails

# Go to the home directory
cd ~

# Clone and install DISCoS master for SRT
discos-get master -s SRT
cd master-srt/SystemMake/
make all install

# Go back to home
cd ~

# Download Redis only if the archive doesn't already exist
if [ ! -f redis-7.0.15.tar.gz ]; then
  wget https://download.redis.io/releases/redis-7.0.15.tar.gz
fi

# Extract and build Redis
tar xzf redis-7.0.15.tar.gz
cd redis-7.0.15/
make BUILD_WITH_LTO=no
sudo make install

# Copy the default configuration file to /etc
sudo cp redis.conf /etc

# Create the redis system user if it doesn't exist
if ! id "redis" &>/dev/null; then
  sudo adduser --system --no-create-home redis
else
  echo "User 'redis' already exists, skipping creation."
fi

# Create the systemd service file for Redis
sudo tee /etc/systemd/system/redis.service > /dev/null <<EOF
[Unit]
Description=Redis In-Memory Data Store
After=network.target

[Service]
ExecStart=/usr/local/bin/redis-server /etc/redis.conf
ExecStop=/usr/local/bin/redis-cli shutdown
Restart=always
User=redis
Group=redis

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable Redis service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable redis
sudo systemctl start redis

# Register Redis with chkconfig and restart the service
sudo chkconfig redis on
sudo service redis restart

# Go back to home
cd ~

# Clone Suricate repository
git clone https://github.com/discos/suricate.git
cd suricate

# Install dependencies
pip install -r requirements.txt
pip install -r testing_requirements.txt
pip install .

# Generate Suricate configuration for SRT
suricate-config -t srt

# Copy the Suricate systemd service file
sudo cp startup/suricate.service /etc/systemd/system/suricate.service

# Initialize the Suricate database
cd ~/suricate/suricate
source .flaskenv
flask db init

# Optional: start the RQ worker manually (commented)
# rqworker -P suricate/ discos-api

# Register Suricate with chkconfig and restart the service
sudo chkconfig suricate on
sudo service suricate restart

# Start discos simulators
# discos-simulators start

# Start discos
# discosup
