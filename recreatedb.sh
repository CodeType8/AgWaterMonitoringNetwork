#!/bin/bash
echo "Recreating database, current data will be deleted"
read -r -p "Are you sure? [y/N] " response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
    echo "Recreating..."
else
    exit 1
fi
sudo systemctl stop myproject
sudo python -c 'import myproject; myproject.recreate_db()'
sudo systemctl start myproject
sudo systemctl enable myproject
