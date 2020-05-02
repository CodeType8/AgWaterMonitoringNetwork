#!/bin/bash
echo "restarting project..."
sudo systemctl stop myproject
sudo systemctl start myproject
sudo systemctl enable myproject
