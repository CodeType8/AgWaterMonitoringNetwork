#!/bin/sh
#Password = AGH2OSystemMaster!
echo "Creating master account in database"
pass=$(python makepassword.py)
sudo -u postgres psql -d agh2odb -c "INSERT INTO users(name, email, irdistrict, defaultloclat, defaultloclong, username, password, isadmin, ismaster) VALUES('Master Account','notreal@gmail.com','All',0.0,0.0,'system','$pass',1,1)"

